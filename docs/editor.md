# textX simple editor support

## Strategy

Allow to use the parsed model or any error (syntax or semantic) occuring
while parsing a model file. Once a model is parsed successfully, we get
correct editor formatting information (syntax highlighting). In case of 
errors, the format information is untouched, only errors are overlaid.


## Model and  meta model support structures

 * metamodel._tx_model_file_access allows to access model sources after
   model parsing. It also allows to hook into any model file access in order
   to provide in-memory model text instead of file data.

## Usage

Example: textX/examples/mini_examples/edit_example.py
![editor example](images/edit_example.png)