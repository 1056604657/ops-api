from apps.cmdb.models import Fields, Resource


def has_resource_verify(params):
    err_message = []
    # 查询出模型的所有字段数据
    fields = list(Fields.objects.filter(model=params.get("model")).values())
    for field in fields:
        if field["required"]:  # 判断数据是否必填
            if params.get("data", {}).get(field["name"], "") != "":
                continue
            else:
                err_message.append(f"""<{field["name"]}> 必填，请确认""")
        if field["is_unique"]:  # 校验数据是否唯一
            v = Resource.objects.raw(
                "select * from cmdb_resource where data->'$.{}' = '{}' and model = {};".format(
                    field["name"],
                    params.get("data", {}).get(field["name"], ""),
                    params.get("model")
                ))
            if len(list(v)) > 0:
                err_message.append(f"""<{field["name"]}> 必须唯一，请确认""")

    if len(err_message) > 0:
        return False, err_message
    return True, ""
