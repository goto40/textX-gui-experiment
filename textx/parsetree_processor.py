from __future__ import unicode_literals
from arpeggio import Terminal

REFERENCE = 'REFERENCE'
KEYWORD = 'KEYWORD'
NAME_VALUE = 'NAME_VALUE'
VALUE = 'VALUE'
COMMENT = 'COMMENT'
SPACES = 'SPACES'


def _is_reference(node, parent_list):
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


def default_classification(node, parent_list):
    if _is_reference(node, parent_list):
        return REFERENCE
    elif isinstance(node, Terminal):
        if parent_list[-1].name.startswith('__asgn'):
            if parent_list[-1].rule._attr_name == 'name':
                return NAME_VALUE
            else:
                return VALUE
        else:
            return KEYWORD
    else:
        return None


def classified_parsetree_nodes(model, classifier=default_classification):
    yield from _classified_parsetree_nodes(model._tx_parser.parse_tree[0],
        classifier)


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
            yield from _classified_parsetree_nodes(node, classifier,
                                                   parent_list + [node])
        else:
            if (node.position_end-node.position)>0:
                yield classifier_result, node, parent_list


def _indent_text(indent):
    return " "*max(0,indent)


def formatter_txt(model,newline_before=[], newline_after=[";","}","{"],
                  indent_inc=["{"],indent_dec=["}"],nospace_before=[";"]):
    """
    Formats a model with indentation.
    Args:
        model: the model to be rendered (formatted)
        newline_before: insert newlines before any of these keywords
        newline_after: insert newlines after any of these keywords
        indent_inc: increase intend after these keywords
        indent_dec: decrease intend after these keywords
        nospace_before: output no space before these keyords

    Returns: teh formatted text

    """

    class FormatterHelper:
        def __init__(self):
            self.indent = 0
            self.begin_of_line = True

        def __call__(self, classifier_result, n, pl):
            spaces = " "
            if (classifier_result == KEYWORD):
                if n.value in nospace_before:
                    spaces = ""
                if n.value in indent_dec:
                    self.indent = self.indent - 1
            if self.begin_of_line:
                spaces = _indent_text(self.indent)
            text = spaces + n.value
            self.begin_of_line = False
            #if (classifier_result == REFERENCE):
            #    text = spaces + ">"+n.value
            if (classifier_result == KEYWORD):
                if n.value in newline_before:
                    text = "\n" + _indent_text(self.indent) + n.value
                if n.value in newline_after:
                    text = spaces + n.value + "\n"
                    self.begin_of_line = True
                if n.value in indent_inc:
                    self.indent = self.indent + 1
            return text

    text = ""
    formatter_helper = FormatterHelper()
    for classifier_result,node,pl in classified_parsetree_nodes(model):
        text += formatter_helper(classifier_result, node, pl)
    return text

