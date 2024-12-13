from apps.tree.models import ServiceTreeModel


class RecursionServiceTree():
    def set_childrens(self, id, nodes):
        children = []  # 保存当前id的子节点
        if isinstance(nodes, list):
            children.extend(nodes)
        for s in children:
            nodes2 = list(ServiceTreeModel.objects.filter(parent=s["id"]).values())
            if len(nodes):  # 如果还有子节点，则进行递归查询
                children_value = self.set_childrens(s["id"], nodes2)
                if children_value is not None:
                    s["children"] = children_value
        if len(children):
            return children
        else:
            return None


recursion_service_tree = RecursionServiceTree()
