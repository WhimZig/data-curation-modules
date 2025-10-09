def print_as_python_dictionary(regex_dict, variable_name):
    regex_str = str(regex_dict)
    regex_str = f"{variable_name} = " + regex_str.replace("\\\\", "\\").replace(
        "'pattern': '", "'pattern': r'"
    )
    print(regex_str)
