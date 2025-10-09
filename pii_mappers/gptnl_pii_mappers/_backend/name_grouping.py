import re
from collections import defaultdict
from itertools import combinations, cycle

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib import cm


def extract_name_parts(full_name: str) -> set[str]:
    """Extracts meaningful parts (first, middle, last names) from a full name string.

    Args:
        full_name (str): The full name string.

    Returns:
        set: A set containing all name parts in lowercase.
    """
    if not isinstance(full_name, str):
        full_name = str(full_name) if full_name is not None else ""
    # Remove punctuation and split into parts
    cleaned_name = re.sub(r"[^\w\s]", "", full_name)
    parts = cleaned_name.lower().split()
    return set(parts) if parts else set()


def group_entities_by_label(entities: list[dict]) -> dict[str, list[dict]]:
    """Groups entities by their labels.

    Args:
        entities (list): List of entity dictionaries with keys like 'text', 'label', etc.

    Returns:
        dict: A dictionary mapping each label to a list of corresponding entities.
    """
    label_to_entities = defaultdict(list)
    for entity in entities:
        label = entity.get("label")
        if label:
            label_to_entities[label].append(entity)
    return label_to_entities


def create_entity_groups(entities: list[dict]) -> dict[str, list[set[int]]]:
    """Groups entities based on shared name parts within the same label.

    Args:
        entities (list): List of entity dictionaries with keys like 'text', 'label', etc.

    Returns:
        dict: A dictionary mapping each label to a list of groups, where each group is a set of entity indices.
    """
    label_to_entities = defaultdict(list)
    for index, entity in enumerate(entities):
        label = entity.get("label")
        if label:
            label_to_entities[label].append((index, entity))

    label_to_groups = defaultdict(list)

    for label, labeled_entities in label_to_entities.items():
        graph = nx.Graph()
        for index, entity in labeled_entities:
            graph.add_node(index, name=entity.get("text", ""))

        name_part_to_entities = defaultdict(set)
        for index, entity in labeled_entities:
            name_parts = extract_name_parts(entity.get("text", ""))
            for part in name_parts:
                name_part_to_entities[part].add(index)

        for entity_indices in name_part_to_entities.values():
            for i, j in combinations(entity_indices, 2):
                graph.add_edge(i, j)

        for component in nx.connected_components(graph):
            label_to_groups[label].append(component)

    return label_to_groups


def assign_masks_to_entities(
    entities: list[dict],
    label_to_groups: dict[str, list[set[int]]],
    entity_types: list[str],
    entity_masks: list[str] | None,
) -> None:
    """Assigns masks to entities based on the provided groups.

    Args:
        entities (list): List of entity dictionaries.
        label_to_groups (dict): Dictionary mapping labels to their respective groups.
        entity_types (list[str]): List of entity type labels.
        entity_masks (list[str] | None): List of masks corresponding to entity types.

    Modifies:
        Each entity in the `entities` list is updated with a 'mask' key.
    """
    index_to_mask = {}

    def get_mask(label):
        if isinstance(entity_masks, list) and label in entity_types:
            return entity_masks[entity_types.index(label)]
        else:
            return f"<{label}>"

    for label, groups in label_to_groups.items():
        for group_num, group in enumerate(groups, start=1):
            mask = f"{get_mask(label)}{group_num}"
            for index in group:
                index_to_mask[index] = mask

    for index, entity in enumerate(entities):
        entity["mask"] = index_to_mask.get(index, "")


def plot_entity_groups(
    entities: list[dict],
    label_to_groups: dict[str, list[set[int]]],
    name_part_to_color: dict[str, tuple] = None,
) -> dict[str, tuple]:
    """Plots the different groups of entities using matplotlib. Each label is visualized in a separate subplot,
    and different groups within a label are color-coded.

    Args:
        entities (list): List of entity dictionaries with keys like 'text', 'label', etc.
        label_to_groups (dict): Dictionary mapping labels to their respective groups.
        name_part_to_color (dict[str, tuple], optional): Mapping from name part to its assigned color. Defaults to None.

    Returns:
        dict[str, tuple]: Updated mapping from name parts to colors.
    """
    if name_part_to_color is None:
        name_part_to_color = {}

    num_labels = len(label_to_groups)
    if num_labels == 0:
        print("No groups to plot.")
        return name_part_to_color

    cols = min(3, num_labels)
    rows = (num_labels + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
    axes = axes.flatten() if num_labels > 1 else [axes]

    color_cycle = cycle(plt.cm.tab20.colors)

    for ax, (label, groups) in zip(axes, label_to_groups.items()):
        G = nx.Graph()
        entity_indices = [
            idx for idx, ent in enumerate(entities) if ent.get("label") == label
        ]
        G.add_nodes_from(entity_indices)

        for group in groups:
            group = list(group)
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    G.add_edge(group[i], group[j])

        group_colors = {}
        for group in groups:
            color = next(color_cycle)
            for node in group:
                group_colors[node] = color
                entity_text = entities[node].get("text", "")
                name_parts = extract_name_parts(entity_text)
                for part in name_parts:
                    if part not in name_part_to_color:
                        name_part_to_color[part] = color

        node_colors = [group_colors.get(node, (0.5, 0.5, 0.5)) for node in G.nodes()]

        cluster_graph = nx.Graph()
        for group_num, group in enumerate(groups):
            cluster_graph.add_node(group_num)

        cluster_pos = nx.spring_layout(cluster_graph, scale=10, seed=42)
        all_pos = {}
        for group_num, group in enumerate(groups):
            subgraph = G.subgraph(group)
            pos = nx.spring_layout(
                subgraph, scale=2, k=10 / (len(groups) ** 0.5), seed=42
            )
            center_offset = cluster_pos[group_num]
            for node, coordinates in pos.items():
                all_pos[node] = coordinates + center_offset

        nx.draw_networkx_nodes(
            G, all_pos, node_color=node_colors, ax=ax, node_size=200, alpha=0.8
        )
        nx.draw_networkx_edges(G, all_pos, ax=ax, alpha=0.5)
        nx.draw_networkx_labels(
            G,
            all_pos,
            labels={node: entities[node].get("text", "") for node in G.nodes()},
            font_size=10,
            ax=ax,
        )

        ax.set_title(f"Label: {label}")
        ax.axis("off")

    for i in range(len(label_to_groups), len(axes)):
        axes[i].axis("off")

    plt.tight_layout()
    plt.show()
    return name_part_to_color


def plot_name_part_connections_by_label(
    entities: list[dict],
    label_to_groups: dict[str, list[set[int]]],
    name_part_to_color: dict[str, tuple],
) -> None:
    """Plots the connections between different name parts for each label separately.
    Each label is visualized in a separate subplot, and the connections represent
    co-occurrences of name parts within entities of that label.

    Args:
        entities (list): List of entity dictionaries with keys like 'text' and 'label'.
        label_to_groups (dict): Dictionary mapping labels to their respective groups.
        name_part_to_color (dict[str, tuple]): Mapping from name part to its assigned color.
    """
    label_to_entities = group_entities_by_label(entities)
    num_labels = len(label_to_entities)
    if num_labels == 0:
        print("No labels found in entities.")
        return

    cols = min(3, num_labels)
    rows = (num_labels + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows))
    axes = axes.flatten() if num_labels > 1 else [axes]

    color_map = cm.get_cmap("tab20", num_labels)
    label_colors = {
        label: color_map(i) for i, label in enumerate(label_to_entities.keys())
    }

    for ax, (label, label_entities) in zip(axes, label_to_entities.items()):
        all_name_parts = [
            extract_name_parts(entity.get("text", "")) for entity in label_entities
        ]
        co_occurrence = defaultdict(int)
        for name_parts in all_name_parts:
            if len(name_parts) < 2:
                continue
            for part1, part2 in combinations(sorted(name_parts), 2):
                co_occurrence[(part1, part2)] += 1

        if not co_occurrence:
            ax.set_title(f"Label: {label} (No connections)")
            ax.axis("off")
            continue

        G = nx.Graph()
        unique_name_parts = {part for parts in all_name_parts for part in parts}
        G.add_nodes_from(unique_name_parts)

        for (part1, part2), count in co_occurrence.items():
            G.add_edge(part1, part2, weight=count)

        weights = [G[u][v]["weight"] for u, v in G.edges()]
        max_weight = max(weights)
        min_weight = min(weights)
        if max_weight != min_weight:
            normalized_weights = [
                1 + (4 * (w - min_weight) / (max_weight - min_weight)) for w in weights
            ]
        else:
            normalized_weights = [3 for _ in weights]

        pos = nx.spring_layout(G, k=0.5, seed=42)
        node_colors = [
            name_part_to_color.get(node, label_colors[label]) for node in G.nodes()
        ]

        nx.draw_networkx_nodes(
            G, pos, node_size=500, node_color=node_colors, alpha=0.7, ax=ax
        )
        nx.draw_networkx_edges(
            G,
            pos,
            width=normalized_weights,
            alpha=0.5,
            edge_color=label_colors[label],
            ax=ax,
        )
        nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif", ax=ax)

        ax.set_title(f"Label: {label}", fontsize=14)
        ax.axis("off")

    for i in range(len(label_to_entities), len(axes)):
        axes[i].axis("off")

    plt.tight_layout()
    plt.show()


def assign_grouped_entity_masks(
    entities: list[dict],
    entity_types: list[str],
    entity_masks: list[str] | None,
    plot_groups: int = 0,
) -> list[dict]:
    """Main function to assign masks to entities and visualize the groups formed.

    Args:
        entities (list): List of entity dictionaries with keys like 'text', 'label', etc.
        entity_types (list[str]): List of entity type labels.
        entity_masks (list[str] | None): List of masks corresponding to entity types.
        plot_groups (bool): Whether to plot the groups. Defaults to True.

    Returns:
        list: The original list of entities with an added 'mask' attribute.
    """
    label_to_groups = create_entity_groups(entities)

    if len(entities) < plot_groups:
        name_part_to_color = plot_entity_groups(entities, label_to_groups)
        plot_name_part_connections_by_label(
            entities, label_to_groups, name_part_to_color
        )

    assign_masks_to_entities(entities, label_to_groups, entity_types, entity_masks)
    return entities


# Sample usage
if __name__ == "__main__":
    # Sample entities
    entities = [
        {"text": "John Doe", "label": "PERSON"},
        {"text": "Hansen Jansen", "label": "PERSON"},
        {"text": "Acme Corporation", "label": "ORGANIZATION"},
        {"text": "Dave Smith", "label": "PERSON"},
        {"text": "Doe Industries", "label": "ORGANIZATION"},
        {"text": "Jane Dane", "label": "PERSON"},
    ]
    # Define entity types and masks if needed
    entity_types = ["PERSON", "ORGANIZATION"]
    entity_masks = ["<PER>", "<ORG>"]
    # Assign masks to entities
    grouped_entities = assign_grouped_entity_masks(entities, entity_types, entity_masks)
    # Print the entities with assigned masks
    for entity in grouped_entities:
        print(entity)
