from __future__ import unicode_literals
from arpeggio import Terminal

# Relevant convenience classes for parse tree processing.
# This classification can be extended.
REFERENCE = 'REFERENCE'
KEYWORD = 'KEYWORD'
NAME_VALUE = 'NAME_VALUE'
VALUE = 'VALUE'
IMPORTURI_VALUE = 'IMPORTURI_VALUE'
COMMENT = 'COMMENT'

def _is_reference(node, parent_list):
    """
    Does the parsetree node represent a reference.
    Args:
        node: the node to be checked
        parent_list: the parents of the nodes (node[-1] is the
        direct parent.
    Returns: True or False
    """
    # detect "references":
    # parent.rule/_tx_class/_tx_attrs/<name>/cont==False & ref=True and mult="1"
    # node: rule/_attr_name=<name>
    if hasattr(node.rule, "_attr_name"):
        name = node.rule._attr_name
        metaattr = parent_list[-1].rule._tx_class._tx_attrs[name]
        if metaattr.ref and not metaattr.cont and metaattr.mult=='1':
            return True
    # detect "references":
    # parent.parent.rule/_tx_class/_tx_attrs/<name>/cont==False & ref=True
    # parent: rule/_attr_name=<name>
    if len(parent_list)>=2:
        if hasattr(parent_list[-1].rule, "_attr_name"):
            name = parent_list[-1].rule._attr_name
            metaattr = parent_list[-2].rule._tx_class._tx_attrs[name]
            if metaattr.ref and not metaattr.cont:
                return True
    return False


def default_classifier(node, parent_list):
    """
    Classifies a parsetree node.
    Args:
        node: the node to be checked
        parent_list: the parents of the nodes (node[-1] is the
        direct parent.
    Returns: The classification result (e.g. REFERENCE, ...).
    """
    if _is_reference(node, parent_list):
        return REFERENCE
    elif isinstance(node, Terminal):
        if parent_list[-1].name.startswith('__asgn'):
            if parent_list[-1].rule._attr_name == 'name':
                return NAME_VALUE
            elif parent_list[-1].rule._attr_name == 'importURI':
                return IMPORTURI_VALUE
            else:
                return VALUE
        else:
            return KEYWORD
    else:
        return None


def classified_parsetree_nodes(model, classifier=default_classifier):
    comments = model._tx_parser.comments
    next_comment_index = 0
    for x in _classified_parsetree_nodes(model._tx_parser.parse_tree[0],
        classifier):
        while next_comment_index<len(comments) and \
                comments[next_comment_index].position<x[1].position:
            yield COMMENT, comments[next_comment_index], []
            next_comment_index+=1
        yield x


def _classified_parsetree_nodes(parsetree_node, classifier, parent_list=None):
    """
    Traverses the parse tree and yields all text fragments given the
    detection logic.

    Must yield iteration over the whole parse tree (and the model text w/o
    spaces).

    Args:
        parsetree_node: node to be processed
        classifier = function to return "logical type" of parstree node,
            e.g., TERMINAL, REFERENCE, ...
        parent_list: parent node (internal)

    Returns: (nothing; yields node with classification)

    """
    if parent_list is None: parent_list = [parsetree_node]
    for node in parsetree_node:
        classifier_result = classifier(node, parent_list)
        if classifier_result == None:
            assert not isinstance(node, Terminal), \
                "unexpected, unclassified terminal"
            for x in _classified_parsetree_nodes(node, classifier,
                                                  parent_list + [node]):
                yield x
        else:
            if (node.position_end-node.position)>0:
                yield classifier_result, node, parent_list

