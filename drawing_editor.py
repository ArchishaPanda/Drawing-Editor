import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import sys
import xml.etree.ElementTree as ET

class FileManager:
    """
    Manages file operations such as saving and opening files for a drawing application.
    """

    def __init__(self):
        """
        Initializes the FileManager with no current file and marks that there are no unsaved changes.
        """
        self.current_file = None
        self.unsaved_changes = False

    def save_file(self, canvas):
        """
        Saves the shapes data to a file. If no file has been specified, it prompts the user to select a file.
        The method assumes that `canvas.shapes` contains string representations of shapes.

        Args:
            canvas: The canvas object containing the shapes data.
        """
        if self.current_file:
            filename = self.current_file
        else:
            filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if not filename:
                return
        canvas.construct_shape_from_shape_object()
        with open(filename, 'w') as file:
            for shape in canvas.shapes:
                file.write(f"{shape}\n")
        self.unsaved_changes = False

    def open_file(self, canvas):
        """
        Opens a file containing shapes data and loads it into the canvas. Warns the user of unsaved changes.

        Args:
            canvas: The canvas object where the shapes will be drawn.
        """
        if self.unsaved_changes:
            if not messagebox.askokcancel("Unsaved Changes", "You have unsaved changes. Do you want to continue?"):
                return
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filename:
            canvas.file_opened = True
            canvas.shapes.clear()
            canvas.delete("all")
            with open(filename, 'r') as file:
                for line in file:
                    canvas.shapes.append(line.strip())
            canvas.redraw_shapes()
            self.current_file = filename
            self.unsaved_changes = False

    def save_to_xml(self,canvas):
        """
        Saves the canvas data to an XML file. If no file is currently specified, it prompts the user for a file location.

        Args:
            canvas: The canvas object containing the shape data.
        """
        if self.current_file:
            filename = self.current_file
        else:
            filename = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
            if not filename:
                return

        root = ET.Element("shapes")

        for shape in canvas.shape_object:
            root.append(ET.fromstring(shape.to_xml()))

        tree = ET.ElementTree(root)
        tree.write(filename)

        self.unsaved_changes = False

    def get_group_hierarchy(self, group, xml):
        group_element = ET.SubElement(xml, "group")  # Create a group element under the root
        for shape in group.indv_shapes:
            shape_element = ET.SubElement(group_element, "shape")  # Create a shape element under the group
            shape_element.text = shape.to_xml()  # Add shape XML representation as text to the shape element
        if group.sub_grps:
            for sg in group.sub_grps:
                self.get_group_hierarchy(sg, xml)  # Update xml recursively
        return ET.tostring(xml, encoding="unicode")

class DrawCanvas(tk.Canvas):
    """
    Canvas widget for drawing shapes and performing various operations like saving, opening, editing, etc.
    """
    def __init__(self, master, **kwargs):
        """
        Initializes the DrawCanvas widget.

        Args:
            master: The parent widget.
            **kwargs: Additional keyword arguments for the Canvas widget.
        """

        super().__init__(master, **kwargs)
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.shapes = []
        self.shape_object = []
        self.selected_shapes = []
        self.properties_text_ids = []
        self.current_tool = None
        self.current_color = "black"
        self.current_style = "s"
        self.start_x = None
        self.start_y = None
        self.current_shape = None
        self.file_manager = FileManager()
        self.file_opened = False
        self.mode = ""
        self.moving = False
        self.canvas_group = []

    def show_popup_message(self, message):
        """
        Displays a popup message.

        Args:
            message (str): The message to be displayed.
        """
        messagebox.showinfo("Message", message)

    def save_file(self):
        """Saves the current drawing to a file."""
        self.file_manager.save_file(self)

    def open_file(self):
        """Opens a drawing file."""
        self.file_manager.open_file(self)

    def save_to_xml(self):
        """Saves the drawing to an XML file."""
        self.file_manager.save_to_xml(self)

    def redraw_shapes(self):
        """
        Redraw all shapes stored in the file. Each shape is parsed from a string format,
        instantiated, and drawn on the canvas.
        """
        for shape_str in self.shapes:
            shape_type, *args = shape_str.split(' ')
            if shape_type == "line":
                x1,y1,x2,y2 = int(args[0]),int(args[1]),int(args[2]),int(args[3])
                color = args[-1]
                self.current_shape = Line(self, x1, y1, x2, y2, color)
                self.shape_object.append(self.current_shape)
                self.current_shape.update(x1,y1,x2, y2)

            elif shape_type == "rectangle":
                x1,x2,y1, y2 = int(args[0]),int(args[1]),int(args[2]),int(args[3])
                color, style = args[-2], args[-1]
                self.current_shape = Rectangle(self, x1, y1,x2,y2, color, style)
                self.shape_object .append(self.current_shape)
                self.current_shape.update(x1,y1,x2, y2)

    def set_mode(self, action):
        """
        Set the operational mode of the canvas.

        Parameters:
            action (str): A string representing the new mode to set. Modes could include 'draw', 'edit',
                          'delete', 'move', etc.
        """
        self.mode = action

    def set_tool(self, tool):
        """
        Set the current drawing tool based on user selection.

        Parameters:
            tool (str): A string representing the drawing tool to use, such as 'line' or 'rectangle'.
        """
        self.current_tool = tool

    def set_color(self, color):
        """
        Set the current drawing color.

        Parameters:
            color (str): A string representing the color to use for new shapes. Colors typically
                         follow CSS color naming (e.g., 'red', 'blue', 'green', etc.).
        """
        self.current_color = color

    def set_style(self, style):
        """
        Set the current drawing style.

        Parameters:
            style (str): A string representing the style to use for new shapes. Styles can be 's' for
                         standard or 'r' for rounded (for rectangles).
        """
        self.current_style = style

    def clear_properties_text(self):
        """
        Clear the properties text displayed beside shapes.
        """
        for text_id in self.properties_text_ids:
            self.delete(text_id)

        self.properties_text_ids.clear()

    def on_click(self, event):
        """
        Handle click events on the canvas. If in 'ready_to_move' mode, move the shapes accordingly.
        Otherwise, clear the selection and properties text.
        """
        self.start_x = event.x
        self.start_y = event.y

        if self.mode == "ready_to_move":
            self.move_shape(event)
            self.mode = ""

        if self.selected_shapes:
            for shape in self.selected_shapes:
                self.itemconfig(shape.shape_id, width=1)
            self.selected_shapes.clear()
            self.clear_properties_text()


    def construct_shape_from_shape_object(self):
        """
        Construct shapes from shape objects and store them as strings in the 'shapes' list.
        """
        self.shapes = []
        for shape in self.shape_object:
            shape_type = self.type(shape.shape_id)
            if shape_type == 'rectangle':
                self.shapes.append(f"{shape_type} {shape.x1} {shape.y1} {shape.x2} {shape.y2} {shape.color} {shape.style}")
            else:
                self.shapes.append(f"{shape_type} {shape.x1} {shape.y1} {shape.x2} {shape.y2} {shape.color}")

    def on_drag(self, event):
        """
        Handle drag events on the canvas. Depending on the mode, perform actions like highlighting shapes,
        drawing new shapes, or moving existing ones.
        """

        if self.mode in ["copy","edit", "delete", "group", "ungroup"]:
            self.highlight_shapes_in_area(self.start_x, self.start_y, event.x, event.y)

        elif self.mode == "move" and self.moving == False:
            self.highlight_shapes_in_area(self.start_x, self.start_y, event.x, event.y)

        elif self.mode == "draw":
            if self.current_tool:
                if self.current_tool == "line":
                    self.current_shape = Line(self, self.start_x, self.start_y, event.x, event.y, self.current_color)
                    self.shape_object .append(self.current_shape)
                elif self.current_tool == "rectangle":
                    self.current_shape = Rectangle(self, self.start_x, self.start_y, event.x, event.y,self.current_color, self.current_style)
                    self.shape_object .append(self.current_shape)
            self.draw_shape(self.start_x,self.start_y,event.x,event.y)

    def draw_shape(self,start_x,start_y,end_x,end_y):
        """
        Draw the shape on the canvas with new coordinates.

        Parameters:
            start_x (int): The starting x-coordinate of the shape.
            start_y (int): The starting y-coordinate of the shape.
            end_x (int): The ending x-coordinate of the shape.
            end_y (int): The ending y-coordinate of the shape.
        """
        if self.current_shape:
            if self.file_opened == False:
                self.current_shape.update(start_x,start_y,end_x,end_y)
            self.current_tool = None

    def on_release(self, event):
        """
        Handle mouse button release events on the canvas, performing actions based on the current mode.

        Parameters:
            event: The event object containing the x, y coordinates of the mouse release event.
        """
        if self.mode == "copy":
            self.copy_shape()
            self.mode = ""

        elif self.mode == "move":
            self.mode = "ready_to_move"

        elif self.mode == "draw":
            if self.current_shape:
                self.current_shape.finalize()
                self.current_shape = None
                self.current_tool=None
                self.mode = ""

        elif self.mode == "edit":
            self.edit_selected_shape()
            self.mode = ""

        elif self.mode == "delete":
            self.delete_shape()
            self.mode = ""

        elif self.mode == "group":
            self.group_shapes()
            self.mode = ""

        elif self.mode == "ungroup":
            self.ungroup_shapes()
            self.mode = ""

        else:
            self.highlight_shapes_in_area(self.start_x, self.start_y, event.x, event.y)

    def highlight_shapes_in_area(self, x1, y1, x2, y2):
        """
        Highlight all shapes that overlap a specified rectangular area and show their properties.

        Parameters:
            x1 (int): The starting x-coordinate of the rectangle.
            y1 (int): The starting y-coordinate of the rectangle.
            x2 (int): The ending x-coordinate of the rectangle.
            y2 (int): The ending y-coordinate of the rectangle.
        """
        if self.properties_text_ids:
            self.delete(self.properties_text_ids)

        overlapping_shapes = self.find_overlapping(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        overlapping_shapes_obj = []
        for shape in overlapping_shapes:
            for shape_obj in self.shape_object:
                if shape == shape_obj.shape_id:
                    overlapping_shapes_obj.append(shape_obj)

        for shape_obj in overlapping_shapes_obj:
            if shape_obj not in self.selected_shapes:
                self.selected_shapes.append(shape_obj)
                if len(shape_obj.groups) > 0:
                    for group in shape_obj.groups:
                        for shape in group.shapes:
                            if shape not in self.selected_shapes:
                                self.selected_shapes.append(shape)

        for shape in self.selected_shapes:
            self.itemconfig(shape.shape_id, width=3)
            x1, y1, x2, y2 = self.bbox(shape.shape_id)
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            shape_type = self.type(shape.shape_id)
            if shape_type == "rectangle":
                color = self.itemcget(shape.shape_id, "outline")
                tags = self.gettags(shape.shape_id)
                if "r" in tags:
                    style = "r"
                else:
                    style = "s"
                properties_text = f"Color: {color}\nStyle: {style}"
            else:
                color = self.itemcget(shape.shape_id, "fill")
                properties_text = f"Color: {color}"

            if self.mode not in ["delete","move","copy", "group", "ungroup"]:
                text = self.create_text(center_x, center_y, text=properties_text, anchor="nw")
                self.properties_text_ids.append(text)

    def delete_shape(self):
        """
        Delete the currently selected shapes from the canvas and internal storage.
        """
        for shape in self.selected_shapes:
            self.delete(shape.shape_id)
            self.shape_object.remove(shape)
        self.selected_shapes.clear()

    def copy_shape(self):
        """
        Create a copy of the selected shapes and position the new shapes at a default offset.
        """
        offset_x, offset_y = 50, 50
        for shape in self.selected_shapes:
            coords = self.coords(shape.shape_id)
            shape_type = self.type(shape.shape_id)

            new_coords = [coord + offset_x if i % 2 == 0 else coord + offset_y for i, coord in enumerate(coords)]
            if shape_type == 'rectangle':
                color = self.itemcget(shape.shape_id, "outline")  # Assuming shapes are filled; adjust attribute as needed
                style = "r" if "r" in self.itemcget(shape.shape_id, "tags") else "s"
                self.current_shape = Rectangle(self, new_coords[0],new_coords[1],new_coords[2],new_coords[3], color, style)
                self.shape_object.append(self.current_shape)
                self.draw_shape(new_coords[0],new_coords[1],new_coords[2],new_coords[3])

            elif shape_type == 'line':
                color = self.itemcget(shape.shape_id, "fill")
                self.current_shape = Line(self, new_coords[0],new_coords[1], new_coords[2],new_coords[3], color)
                self.shape_object .append(self.current_shape)
                self.draw_shape(new_coords[0],new_coords[1],new_coords[2],new_coords[3])

    def move_shape(self,event):
        """
        Move the currently selected shapes based on the mouse drag event.

        Parameters:
            event: The event object containing the x, y coordinates of the mouse event.
        """
        self.moving = True
        if self.selected_shapes:
            shape = self.selected_shapes[0]
            first_shape_id = self.selected_shapes[0].shape_id
            initial_coords = self.coords(first_shape_id)
            dx, dy = event.x - ((initial_coords[2] + initial_coords[0])/2), event.y -((initial_coords[3] + initial_coords[1])/2)

            self.shape_object.remove(shape)
            self.move(shape.shape_id, dx, dy)

            shape.x1 += dx
            shape.x2 += dx
            shape.y1 += dy
            shape.y2 += dy

            self.shape_object.append(shape)

        for shape in self.selected_shapes[1:]:
            self.shape_object.remove(shape)
            self.move(shape.shape_id, dx, dy)

            shape.x1 += dx
            shape.x2 += dx
            shape.y1 += dy
            shape.y2 += dy

            self.shape_object.append(shape)

    def edit_selected_shape(self):
        """
        Edit properties of the selected shape if only one shape is selected.
        """
        if len(self.selected_shapes) > 1:
            self.show_popup_message("Multiple objects cannot be edited at once")
            return

        shape_id = self.selected_shapes[0].shape_id
        shape_type = self.type(shape_id)

        if shape_type == 'rectangle':
            new_color = simpledialog.askstring("Input", "Enter new color (e.g., red, blue, green):", parent=self.master)

            new_style = simpledialog.askstring("Input", "Enter new style (s or r):", parent=self.master)
            if new_style and new_color:
                self.update_rectangle_style(shape_id, new_style,new_color)

        elif shape_type == 'line':
            new_color = simpledialog.askstring("Input", "Enter new color (e.g., red, blue, green):", parent=self.master)
            if new_color:
                self.itemconfig(shape_id, fill=new_color)

        self.delete_shape()
        self.clear_properties_text()

    def update_rectangle_style(self, shape_id, style, color):
        """
        Update the style and color of a rectangle shape.

        Parameters:
            shape_id (int): The ID of the shape to be updated.
            style (str): The style ('r' for rounded, 's' for sharp) of the rectangle.
            color (str): The new color for the rectangle.
        """
        coords = self.coords(shape_id)
        self.current_shape = Rectangle(self, coords[0], coords[1], coords[2], coords[3],color,style)
        if style == 'r':
            self.current_shape.draw_rounded_rectangle(coords[0], coords[1], coords[2], coords[3], radius=20, outline=color, fill='')
        elif style == 's':
            self.current_shape = self.create_rectangle(coords[0], coords[1], coords[2], coords[3], outline=color)

    def group_shapes (self):
        """
        Group the selected shapes together.
        """
        if len(self.selected_shapes) > 1:
            new_group = Group()
            for shape in self.selected_shapes:
                new_group.add_shapes(shape)
                shape.add_group(new_group)
            self.canvas_group.append(new_group)
            self.show_popup_message("Group Formed")

    def ungroup_shapes (self):
        """
        Ungroup the selected shapes from their current group.
        """
        if self.selected_shapes:
            flag = 0
            if self.selected_shapes[0].groups:
                g = self.selected_shapes[0].groups[-1]
                for shape in self.selected_shapes:
                    if shape.groups:
                        if shape.groups[-1] != g:
                            flag = 1
                            break
                    else:
                        flag = 1
                        break
            else:
                flag = 1
            if flag == 0:
                for shape in self.selected_shapes:
                    shape.groups = shape.groups[:-1]
                    g.remove_shapes(shape)
                self.show_popup_message("Objects Ungrouped")
            else:
                self.show_popup_message("The selected elements do not belong to a common group")


class Group:
    """
    A class representing a group of shapes.

    Attributes:
        shapes (list): A list containing the shapes that belong to this group.
    """
    def __init__(self):
        """
        Initialize a new Group object.
        """
        self.shapes = []
        self.indv_shapes = []
        self.sub_grps = []

    def add_shapes(self, Shape):
        """
        Add a shape to this group.

        Parameters:
            Shape: The shape object to be added to the group.
        """
        self.shapes.append(Shape)
        if Shape.groups:
            g = Shape.groups[-1]
            if g not in self.sub_grps:
                self.sub_grps.append(g)
        else:
                self.indv_shapes.append(Shape)

    def remove_shapes(self, Shape):
        """
        Remove a shape from this group.

        Parameters:
            Shape: The shape object to be removed from the group.
        """
        self.shapes.remove(Shape)

class Shape:
    """
    A base class representing a general shape object in a canvas.

    Attributes:
        canvas: The canvas on which the shape is drawn.
        x1 (int): The starting x-coordinate of the shape.
        y1 (int): The starting y-coordinate of the shape.
        x2 (int): The ending x-coordinate of the shape.
        y2 (int): The ending y-coordinate of the shape.
        color (str): The color of the shape.
        shape_id: The unique identifier for the shape in the canvas, can be None if not drawn yet.
        groups (list): A list of groups that this shape is part of.
    """
    def __init__(self, canvas, x1,y1,x2,y2, color):
        """
        Initialize a new Shape object with specified parameters.

        Parameters:
            canvas: The canvas object where this shape will be drawn.
            x1 (int): The starting x-coordinate of the shape.
            y1 (int): The starting y-coordinate of the shape.
            x2 (int): The ending x-coordinate of the shape.
            y2 (int): The ending y-coordinate of the shape.
            color (str): The color of the shape.
        """
        self.canvas = canvas
        self.color = color
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.shape_id = None
        self.groups = []

    def add_group(self, Group):
        """
        Add a group to the list of groups to which this shape belongs.

        Parameters:
            group: The group object to add this shape to.
        """
        self.groups.append(Group)

    def update(self):
        """
        Update the properties of the shape. This method must be implemented by subclasses.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("This method should be overridden by subclasses")

    def finalize(self):
        """
        Perform any final adjustments after the shape is fully created and drawn.

        This method provides a hook for any cleanup or final setup required for the shape
        once it has been drawn on the canvas. This method does nothing by default and
        can be overridden by subclasses.
        """
        pass

class Line(Shape):
    """
    A subclass of Shape specifically for drawing lines on a canvas.

    Inherits from:
        Shape: The base class for shapes drawn on a canvas.
    """
    def __init__(self, canvas, start_x, start_y, end_x, end_y, color):
        """
        Initialize a new Line object.

        Parameters:
            canvas: The canvas on which the line will be drawn.
            start_x (int): The x-coordinate of the start point of the line.
            start_y (int): The y-coordinate of the start point of the line.
            end_x (int): The x-coordinate of the end point of the line.
            end_y (int): The y-coordinate of the end point of the line.
            color (str): The color of the line.
        """
        super().__init__(canvas, start_x, start_y, end_x, end_y, color)

    def update(self, start_x,start_y,end_x, end_y):
        """
        Update the position and draw the line on the canvas.

        Parameters:
            start_x (int): The new x-coordinate of the start point.
            start_y (int): The new y-coordinate of the start point.
            end_x (int): The new x-coordinate of the end point.
            end_y (int): The new y-coordinate of the end point.
        """
        if self.shape_id:
            self.canvas.delete(self.shape_id)
        self.shape_id = self.canvas.create_line(start_x, start_y, end_x, end_y, fill=self.color)

    def to_xml(self):
        """
        Convert the line object to XML format for saving.

        Returns:
            str: A string representing the line in XML format.
        """
        xml = "<line>\n"
        xml += f"\t<begin>\n\t\t<x>{self.x1}</x>\n\t\t<y>{self.y1}</y>\n\t</begin>\n"
        xml += f"\t<end>\n\t\t<x>{self.x2}</x>\n\t\t<y>{self.y2}</y>\n\t</end>\n"
        xml += f"\t<color>{self.color}</color>\n</line>\n"
        return xml

class Rectangle(Shape):
    """
    A subclass of Shape specifically for drawing rectangles on a canvas.
    This class can create both regular and rounded rectangles based on the style.

    Inherits from:
        Shape: The base class for shapes drawn on a canvas.
    """

    def __init__(self, canvas, start_x, start_y, end_x, end_y, color, style):
        """
        Initialize a new Rectangle object.

        Parameters:
            canvas: The canvas on which the rectangle will be drawn.
            start_x (int): The x-coordinate of the upper-left corner of the rectangle.
            start_y (int): The y-coordinate of the upper-left corner of the rectangle.
            end_x (int): The x-coordinate of the lower-right corner of the rectangle.
            end_y (int): The y-coordinate of the lower-right corner of the rectangle.
            color (str): The color of the rectangle's outline.
            style (str): The style of the rectangle ('s' for sharp corners, 'r' for rounded corners).
        """
        super().__init__(canvas, start_x, start_y, end_x, end_y, color)
        self.style = style

    def update(self, start_x,start_y,end_x, end_y):
        """
        Update the position and redraw the rectangle on the canvas.

        Parameters:
            start_x (int): The new x-coordinate of the upper-left corner.
            start_y (int): The new y-coordinate of the upper-left corner.
            end_x (int): The new x-coordinate of the lower-right corner.
            end_y (int): The new y-coordinate of the lower-right corner.
        """
        if self.shape_id:
            self.canvas.delete(self.shape_id)
        if self.style == "s":
            self.shape_id = self.canvas.create_rectangle(start_x, start_y, end_x, end_y, outline=self.color)
        elif self.style == "r":
            self.shape_id = self.draw_rounded_rectangle(start_x, start_y, end_x, end_y, radius=20, outline=self.color, fill='')

    def draw_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """
        Draw a rounded rectangle on the canvas.

        Parameters:
            x1 (int): The x-coordinate of the upper-left corner.
            y1 (int): The y-coordinate of the upper-left corner.
            x2 (int): The x-coordinate of the lower-right corner.
            y2 (int): The y-coordinate of the lower-right corner.
            radius (int): The radius of the corner curves.
            kwargs: Additional keyword arguments for canvas.create_polygon.

        Returns:
            int: Canvas ID of the created polygon representing the rounded rectangle.
        """
        points = [x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1, x2, y1,
                  x2, y1 + radius, x2, y1 + radius, x2, y2 - radius, x2, y2 - radius, x2, y2,
                  x2 - radius, y2, x2 - radius, y2, x1 + radius, y2, x1 + radius, y2, x1, y2,
                  x1, y2 - radius, x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1]
        return self.canvas.create_polygon(points, **kwargs, smooth=True)

    def to_xml(self):
        """
        Convert the rectangle object to XML format for saving.

        Returns:
            str: A string representing the rectangle in XML format.
        """
        xml = "<rectangle>\n"
        xml += f"\t<upper-left>\n\t\t<x>{self.x1}</x>\n\t\t<y>{self.y1}</y>\n\t</upper-left>\n"
        xml += f"\t<lower-right>\n\t\t<x>{self.x2}</x>\n\t\t<y>{self.y2}</y>\n\t</lower-right>\n"
        xml += f"\t<color>{self.color}</color>\n"
        xml += f"\t<corner>{self.style}</corner>\n"
        xml += "</rectangle>\n"
        return xml


class DrawingApp:
    """
    A simple drawing application built using Tkinter. It allows users to draw, edit,
    and manage simple graphical objects such as lines and rectangles on a canvas.
    """
    def __init__(self, master):
        """
        Initialize the DrawingApp with a main window.

        Parameters:
            master (Tk): The main window for the application, typically an instance of Tk.
        """
        self.master = master
        self.master.title("Drawing App")
        self.canvas = DrawCanvas(self.master, width=1000, height=1000, bg="white")
        self.canvas.pack()

        self.create_menu()

        if len(sys.argv) > 1:
            self.canvas.file_manager.current_file = sys.argv[1]
            # self.canvas.open_file()

    def create_menu(self):
        """
        Create the menu bar and its sub-menus for the application, including drawing tools
        and file management options.
        """
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        draw_menu = tk.Menu(menubar, tearoff=0)
        file_menu = tk.Menu(menubar, tearoff=0)

        line_menu = tk.Menu(draw_menu, tearoff=0)
        color_menu_line = tk.Menu(line_menu, tearoff=0)
        color_menu_line.add_command(label="Black", command=lambda: (self.canvas.set_color("black"), self.canvas.set_tool("line"),self.canvas.set_mode("draw")))
        color_menu_line.add_command(label="Blue", command=lambda: (self.canvas.set_color("blue"),self.canvas.set_tool("line"),self.canvas.set_mode("draw")))
        color_menu_line.add_command(label="Green", command=lambda: (self.canvas.set_color("green"),self.canvas.set_tool("line"),self.canvas.set_mode("draw")))
        color_menu_line.add_command(label="Red", command=lambda: (self.canvas.set_color("red"),self.canvas.set_tool("line"),self.canvas.set_mode("draw")))
        line_menu.add_cascade(label="Color", menu=color_menu_line)
        draw_menu.add_cascade(label="Line", menu=line_menu)

        rectangle_menu = tk.Menu(draw_menu, tearoff=0)
        color_menu_rect = tk.Menu(rectangle_menu, tearoff=0)
        color_menu_rect.add_command(label="Black", command=lambda: (self.canvas.set_color("black"),self.canvas.set_tool("rectangle"),self.canvas.set_mode("draw")))
        color_menu_rect.add_command(label="Blue", command=lambda: (self.canvas.set_color("blue"),self.canvas.set_tool("rectangle"),self.canvas.set_mode("draw")))
        color_menu_rect.add_command(label="Green", command=lambda: (self.canvas.set_color("green"),self.canvas.set_tool("rectangle"),self.canvas.set_mode("draw")))
        color_menu_rect.add_command(label="Red", command=lambda: (self.canvas.set_color("red"),self.canvas.set_tool("rectangle"),self.canvas.set_mode("draw")))
        rectangle_menu.add_cascade(label="Color", menu=color_menu_rect)
        style_menu = tk.Menu(rectangle_menu, tearoff=0)
        style_menu.add_command(label="Square Corners", command=lambda: (self.canvas.set_style("s"),self.canvas.set_tool("rectangle"),self.canvas.set_mode("draw")))
        style_menu.add_command(label="Rounded Corners", command=lambda: (self.canvas.set_style("r"),self.canvas.set_tool("rectangle"),self.canvas.set_mode("draw")))
        rectangle_menu.add_cascade(label="Style", menu=style_menu)
        draw_menu.add_cascade(label="Rectangle", menu=rectangle_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Copy", command=lambda: (self.canvas.set_mode("copy")))
        edit_menu.add_command(label="Move", command=lambda: (self.canvas.set_mode("move")))
        edit_menu.add_command(label="Delete", command=lambda: (self.canvas.set_mode("delete")))
        edit_menu.add_command(label="Edit", command=lambda: (self.canvas.set_mode("edit")))
        edit_menu.add_command(label="Group Objects", command=lambda: (self.canvas.set_mode("group")))
        edit_menu.add_command(label="Ungroup Objects", command=lambda: (self.canvas.set_mode("ungroup")))


        file_menu.add_command(label="Open", command=self.canvas.open_file)
        file_menu.add_command(label="Save", command=self.canvas.save_file)
        file_menu.add_command(label="Export", command=self.canvas.save_to_xml)

        menubar.add_cascade(label="Draw", menu=draw_menu)
        menubar.add_cascade(label="Actions", menu=edit_menu)
        menubar.add_cascade(label="File", menu=file_menu)

def main():
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()