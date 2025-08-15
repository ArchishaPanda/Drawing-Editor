# Drawing-Editor
Contains implementation for a drawing editor developed in Python

## How to run the file:

1. Run the following command in the terminal:

    `python3 drawing_editor.py`

2. Following libraries have been used:

    `import tkinter as tk`

    `from tkinter import filedialog, messagebox, simpledialog`

    `import sys`

    `import xml.etree.ElementTree as ET`

## How to use the prototype:

1. On running the file, a canvas window opens with 3 menus in the title bar - draw, actions and file.
2. The Draw menu has options to draw a line and rectangle which further has suboptions for colour for line and colour and style for rectangle.
    - the colour/style can be selected and then shape can be drawn on the desired area on the canvas by dragging the cursor.
3. The Actions menu has the options copy,move,delete,edit,group and ungroup objects.
    - For copy:
        - Select copy from the menu
        - Drag to select the shapes to be copied. If shape is part of a group, all shapes in group will be selected.
        - Copied objects will be displayed with some offset.
    - For move:
        - Select move from the menu
        - Drag to select the shapes to be moved. If shape is part of a group, all shapes in group will be selected.
        - Click on new location. Objects will be moved
    - For delete:
        - Select delete from the menu
        - Drag to select the shapes to be deleted. If shape is part of a group, all shapes in group will be selected and deleted.
    - For edit:
        - Select edit from the menu
        - Drag to select the shapes to be edited. 
        - If the shape is a line, dialog box will be displayed asking for new color. If rectangle, new style will also be asked.
        - On clicking on OK, the updated shape will be displayed.
    - For group:
        - Select group from the menu
        - Drag to select the shapes to be grouped. 
        - On successful grouping, a pop up message will be displayed.
    - For ungroup:
        - Select ungroup from the menu
        - Drag to select the shapes to be ungrouped. Ungrouping will be done according to hierarchy mentioned in requirements.
        - On successful ungrouping, a pop up message will be displayed.

4. The File menu has the options of save,export,open which if selected opens the dialogue box to create/open the desired file.

## Assumptions

1. The PUML code for the class diagram has been included as class_diagram.txt file.



