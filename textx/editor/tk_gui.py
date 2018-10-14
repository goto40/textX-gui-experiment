from __future__ import unicode_literals
from textx.scoping import MetaModelProvider
import textx.editor.parsetree_processor as pp
import codecs
import tkinter as tk


def edit(model_filename, meta_model=None):
    if meta_model is None:
        MetaModelProvider.get_metamodel(None, model_filename)
    if meta_model is None:
        raise Exception("unexpected: no meta model available for {}.".format(
            model_filename
        ))
    e=Editor(meta_model)
    e.edit(model_filename)


# from https://stackoverflow.com/questions/40617515/python-tkinter-text-modified-callback
# create a proxy for the underlying widget
class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        """A text widget that report on internal widget commands"""
        tk.Text.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)
        if command in ("insert", "delete", "replace"):
            self.event_generate("<<TextModified>>")
        return result

class Editor:
    def __init__(self, mm):
        self.mm = mm
        # GUI setup
        self.fontname="Courier"
        self.root = tk.Tk()
        SV = tk.Scrollbar(self.root, orient=tk.VERTICAL)
        SH = tk.Scrollbar(self.root, orient=tk.HORIZONTAL)
        self.T = CustomText(self.root, height=25, width=80, wrap=tk.NONE)
        SV.pack(side=tk.RIGHT, fill=tk.Y)
        SH.pack(side=tk.BOTTOM, fill=tk.X)
        SV.config(command=self.T.yview)
        SH.config(command=self.T.xview)
        self.T.config(yscrollcommand=SV.set)
        self.T.config(xscrollcommand=SH.set)
        self.T.config(font=(self.fontname,12),foreground='black')
        self.T.pack(fill=tk.BOTH, expand=1)
        self.T.bind("<<TextModified>>", self.onModification)

    def onModification(self, event=None):
        self.mm._tx_model_file_access.set_text_for_file(
            self.model._tx_filename, self.T.get("1.0",tk.END))
        try:
            self.model = self.mm.model_from_file(self.model._tx_filename)
            print("modified!")
            self.analyze_and_set_tags()
            print("modifications updated...")
        except Exception as e:
            print("modified, parse/validation error: {}".format(str(e)))


    def analyze_and_set_tags(self):
        for tag in self.T.tag_names():
            self.T.tag_delete(tag)

        # first test: color some aspects
        pt = self.model._tx_parser.parse_tree[0]
        r2pos1 = lambda o : \
            self.model._tx_parser.pos_to_linecol(o.position-1)
        r2pos2 = lambda o : \
            self.model._tx_parser.pos_to_linecol(o.position_end-1)

        for nodeclass, node, parents in pp.classified_parsetree_nodes(
                self.model):
            self.T.tag_add(nodeclass,
                      '{}.{}'.format(*r2pos1(node)),
                      '{}.{}'.format(*r2pos2(node)))

        self.T.tag_config(pp.KEYWORD, foreground='black',
                     font=(self.fontname, 12, 'bold') )
        self.T.tag_config(pp.VALUE, foreground='green',
                     font=(self.fontname, 12, 'normal') )
        self.T.tag_config(pp.REFERENCE, foreground='blue',
                     font=(self.fontname, 12, 'bold'))
        self.T.tag_config(pp.NAME_VALUE, foreground='magenta',
                     font=(self.fontname, 12, 'normal') )
        self.T.tag_config(pp.IMPORTURI_VALUE, foreground='red',
                     font=(self.fontname, 12, 'normal') )
        self.T.tag_config(pp.IMPORTURI_VALUE, foreground='red',
                     font=(self.fontname, 12, 'normal') )
        self.T.tag_config(pp.COMMENT, foreground='gray',
                     font=(self.fontname, 12, 'normal') )

    def edit(self, model_filename):
        with codecs.open(model_filename, 'r', encoding='utf-8') as f:
            model_str = f.read()
        self.mm._tx_model_file_access.enable_auto_buffer(True)
        # TODO: set the flag for all meta models involved in this editor
        # (-> MetaModelProvider may yield all these objects).
        self.model = self.mm.model_from_file(model_filename)
        self.T.insert(tk.END, self.mm._tx_model_file_access.
                      get_buffered_text_from_model(self.model))
        self.analyze_and_set_tags()

        # run GUI
        tk.mainloop()
