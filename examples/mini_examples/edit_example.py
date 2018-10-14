from textx import metamodel_from_str
from textx.exceptions import TextXSemanticError
from textx.scoping.tools import get_location
from textx.scoping.providers import RelativeName, FQN
import textx.editor.tk_gui as gui
import sys
# ------------------------------------
# GRAMMAR
#
meta_model = metamodel_from_str('''
    Model: aspects+=Aspect scenarios+=Scenario testcases+=Testcase;
    Scenario: 'SCENARIO' name=ID 'BEGIN' 
        configs+=Config
    'END';
    Config: 'CONFIG' name=ID 'HAS' '(' haves*=[Aspect] ')';
    Aspect: 'ASPECT' name=ID;
    Testcase: 'TESTCASE' name=ID 'BEGIN'
        'USES' scenario=[Scenario] 'WITH' config=[Config]
        'NEEDS' '(' needs*=[Aspect] ')'
    'END';
    Comment: /\/\/.*/;
''')

# ------------------------------------
# SCOPING
#
meta_model.register_scope_providers({
    '*.*': FQN(),
    'Testcase.config': RelativeName('scenario.configs')
})

# ------------------------------------
# VALIDATION
#
def check_testcase(testcase):
    """
    checks that the config used by the testcase fulfills its needs
    """
    for need in testcase.needs:
        if need not in testcase.config.haves:
            raise TextXSemanticError("{}: {} not found in {}.{}".format(
                    testcase.name,
                    need.name,
                    testcase.scenario.name,
                    testcase.config.name
                    ), **get_location(testcase))

meta_model.register_obj_processors({
        'Testcase': check_testcase
})

# ------------------------------------
# EXAMPLE: RUN THE EDITOR
# run this file with the parameter edit_example.model.
# ("edit_example.model" is a file side-by-side to this program.)
#
if __name__ == '__main__':
    if len(sys.argv)==2:
        fn = sys.argv[1] # e.g. 'edit_example.model'
        gui.edit(fn, meta_model)
