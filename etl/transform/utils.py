def join_data(data_1, data_2, id_field_1, id_field_2, prefix_1='', prefix_2=''):
    dict_1 = {
        entry[id_field_1]: {prefix_1 + attr_name: attr for attr_name, attr in entry}
        for entry in data_1
    }
    dict_2 = {
        entry[id_field_2]: {prefix_2 + attr_name: attr for attr_name, attr in entry}
        for entry in data_2
    }
    return [{**entry, **dict_2[paper_id]} for paper_id, entry in dict_1.items()]
