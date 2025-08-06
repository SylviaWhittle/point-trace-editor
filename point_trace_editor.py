#!/usr/bin/env python3
"""TKinter editor for point traces"""

import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip


class PointTraceEditor:
    """Class for management of point trace rendering and editing."""

    def __init__(self, main_window):
        # Create main window
        self.main_window = main_window
        self.main_window.title("Point Trace Editor")
        self.main_window.geometry("800x700")

        # list to store points
        self.points = []
        # drawing options for points
        self.point_colour = "black"
        self.point_line_colour = "black"
        self.point_text_colour = "black"
        self.point_dragging_colour = "red"
        self.point_radius = 3

        # drag state tracking
        self.dragging = False
        self.drag_point_index = None
        self.drag_start_x = 0
        self.drag_start_y = 0

        # mouse position tracking for delete functionality
        self.mouse_x = 0
        self.mouse_y = 0

        # Create main frame - to hold all widgets
        main_frame = ttk.Frame(main_window, padding="10")
        # Set up a grid layout for the main frame
        # Sticky with all directions means the frame will expand to fill the window
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights - allows expansion when the window is resized
        main_window.columnconfigure(0, weight=1)
        main_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title - a label at the top of the main frame
        title_label = ttk.Label(
            main_frame, text="Point Trace Editor", font=("Arial", 16, "bold")
        )
        # Grid the title label to span two columns. pady adds vertical gaps.
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Canvas for drawing points
        self.canvas = tk.Canvas(
            main_frame, bg="grey", width=600, height=400, relief="sunken", bd=2
        )
        # Create a grid layout for the canvas, so it can be resized with the window.
        self.canvas.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        # Bind left mouse to click event
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        # Bind mouse motion and release for dragging
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        # Bind mouse motion to track cursor position
        self.canvas.bind("<Motion>", self.on_mouse_move)

        # Make canvas focusable and bind keyboard events
        self.canvas.focus_set()
        self.canvas.bind("<Key>", self.on_key_press)

        # buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Buttons
        ttk.Button(
            buttons_frame, text="Clear All Points", command=self.clear_points
        ).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(
            buttons_frame, text="Copy Coordinates", command=self.copy_coordinates
        ).grid(row=0, column=1, padx=5)

        # Coordinates display frame. padding adds space around the frame.
        coord_frame = ttk.LabelFrame(main_frame, text="Coordinates", padding="10")
        coord_frame.grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        coord_frame.columnconfigure(0, weight=1)
        coord_frame.rowconfigure(0, weight=1)

        # Text widget for displaying coordinates
        self.terminal_text = tk.Text(coord_frame, height=8, width=70, wrap=tk.WORD)
        self.terminal_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar for text widget
        scrollbar = ttk.Scrollbar(
            coord_frame, orient="vertical", command=self.terminal_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.terminal_text.configure(yscrollcommand=scrollbar.set)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(
            "Click: place/drag points or insert on lines, 'd': delete point near cursor"
        )
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief="sunken", anchor="w"
        )
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))

        # initial update of terminal and canvas
        self.update_terminal()
        self.redraw_canvas()

    def on_canvas_click(self, event):
        """Run whenever the canvas is clicked."""
        x, y = event.x, event.y

        # Check if clicking on an existing point
        clicked_point_index = self.find_point_at_position(x, y)

        if clicked_point_index is not None:
            # Start dragging existing point
            self.dragging = True
            self.drag_point_index = clicked_point_index
            self.drag_start_x = x
            self.drag_start_y = y
            self.status_var.set(f"Dragging point {clicked_point_index + 1}")
        else:
            # Check if clicking on a line segment to insert a point
            line_segment = self.find_line_at_position(x, y)

            if line_segment is not None:
                # Insert new point between the two points of the line segment
                insert_index = line_segment + 1
                self.points.insert(insert_index, (x, y))
                self.redraw_canvas()
                self.update_terminal()
                self.status_var.set(
                    f"Point inserted at position {insert_index + 1}: ({x}, {y})"
                )
            else:
                # Create new point at end of list
                self.points.append((x, y))
                self.redraw_canvas()
                self.update_terminal()
                self.status_var.set(f"Point {len(self.points)} placed at ({x}, {y})")

    def on_canvas_drag(self, event):
        """Handle mouse drag events."""
        if self.dragging and self.drag_point_index is not None:
            # Update the position of the dragged point
            x, y = event.x, event.y
            self.points[self.drag_point_index] = (x, y)
            self.redraw_canvas()
            self.status_var.set(
                f"Moving point {self.drag_point_index + 1} to ({x}, {y})"
            )

    def on_canvas_release(self, event):
        """Handle mouse release events."""
        if self.dragging:
            x, y = event.x, event.y
            self.points[self.drag_point_index] = (x, y)
            self.redraw_canvas()
            self.update_terminal()
            self.status_var.set(
                f"Point {self.drag_point_index + 1} moved to ({x}, {y})"
            )

            # Reset drag state
            self.dragging = False
            self.drag_point_index = None

    def on_mouse_move(self, event):
        """Track mouse position for delete functionality."""
        self.mouse_x = event.x
        self.mouse_y = event.y

    def on_key_press(self, event):
        """Handle keyboard events."""
        if event.keysym.lower() == "d":
            self.delete_point_at_mouse()

    def delete_point_at_mouse(self):
        """Delete point near the current mouse position."""
        point_index = self.find_point_at_position(self.mouse_x, self.mouse_y)

        if point_index is not None:
            deleted_point = self.points.pop(point_index)
            self.redraw_canvas()
            self.update_terminal()
            self.status_var.set(
                f"Deleted point at ({deleted_point[0]}, {deleted_point[1]})"
            )
        else:
            self.status_var.set("No point near mouse cursor to delete")

    def find_point_at_position(self, x, y):
        """Find if there's a point at the given position (within click radius)."""
        click_radius = self.point_radius + 5  # A bit larger than the visual radius

        for i, (px, py) in enumerate(self.points):
            # Calculate distance from click to point center
            distance = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
            if distance <= click_radius:
                return i
        return None

    def find_line_at_position(self, x, y):
        """
        Return the index of the first point of a point pair that forms a line segment that is near the given
        position.
        
        Parameters:
        -----------
        x : int
            The x-coordinate of the mouse click position.
        y : int
            The y-coordinate of the mouse click position.
        
        Returns:
        --------
        int or None
            The index of the first point of the line segment if found, otherwise None.
        """
        if len(self.points) < 2:
            return None

        line_click_tolerance = 5

        # Iterate through each point pair combo to find line segments and then check if the cursor is near any
        # line segments
        # Note that if there are two line segments that meet this criteria, the first one will be returned.
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]

            # Calculate distance from point to line segment
            if (
                self.point_to_line_distance(x, y, x1, y1, x2, y2)
                <= line_click_tolerance
            ):
                return i
        return None

    def point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """Calculate the shortest distance from a point to a line segment."""

        # To find distance, need to find closest point on the line segment
        # first, check if the line is of zero length
        if (x1 == x2) and (y1 == y2):
            # Line segment is a point, return distance to that point
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        else:
            # Find the line segment vector
            line_vec_x = x2 - x1
            line_vec_y = y2 - y1
            # Find the point vector from the start of the line segment
            point_vec_x = px - x1
            point_vec_y = py - y1
            # Calculate the projection of the point vector onto the line segment
            line_length_squared = line_vec_x**2 + line_vec_y**2
            dot_product_point_line = point_vec_x * line_vec_x + point_vec_y * line_vec_y
            # Projection of the point vector P onto the line segment vector L is:
            # P dot L / ||L||
            # This will yeild a scalar value that tells us how far along the line segment the point projects,
            # but this can be negative or greater than the length of the line segment.
            # If it's negative, then the point lies before the start of the segment, and if it's greater than 1, then
            # it lies beyong the end of the segment.
            # So we clamp it.
            projection = dot_product_point_line / line_length_squared
            projection = max(0, min(1, projection))
            # This allows us to find the closest point on the line segment
            closest_x = x1 + projection * line_vec_x
            closest_y = y1 + projection * line_vec_y
            # Now can calculate distance point to closest point on line segment
            distance = ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
            return distance

    def clear_points(self):
        """Clear all placed points."""
        self.points.clear()
        self.redraw_canvas()
        self.update_terminal()
        self.status_var.set("All points cleared")

    def redraw_canvas(self):
        """Redraw all points and lines on the canvas."""
        # Clear the entire canvas
        self.canvas.delete("all")

        # Draw lines between consecutive points
        if len(self.points) > 1:
            for i in range(len(self.points) - 1):
                x1, y1 = self.points[i]
                x2, y2 = self.points[i + 1]
                self.canvas.create_line(
                    x1, y1, x2, y2, fill=self.point_line_colour, width=2
                )

        # Draw all points
        for i, (x, y) in enumerate(self.points, 1):
            # Determine point color (highlight if being dragged)
            point_color = (
                self.point_dragging_colour
                if (self.dragging and self.drag_point_index == i - 1)
                else self.point_colour
            )
            point_outline = "black"

            # Draw point circle
            self.canvas.create_oval(
                x - self.point_radius,
                y - self.point_radius,
                x + self.point_radius,
                y + self.point_radius,
                fill=point_color,
                outline=point_outline,
                width=2 if (self.dragging and self.drag_point_index == i - 1) else 1,
            )

            # Add point number label
            self.canvas.create_text(
                x + 10,
                y - 10,
                text=str(i),
                fill=self.point_text_colour,
                font=("Arial", 8, "bold"),
            )

    def update_terminal(self):
        """Update the terminal text widget."""
        self.terminal_text.delete(1.0, tk.END)

        if not self.points:
            self.terminal_text.insert(
                tk.END,
                "No points placed.",
            )
            return

        # Display points in a readable format
        self.terminal_text.insert(tk.END, "Placed Points:\n")
        self.terminal_text.insert(tk.END, "-" * 40 + "\n")

        for i, (x, y) in enumerate(self.points, 1):
            self.terminal_text.insert(tk.END, f"Point {i}: ({x}, {y})\n")

        # print copy-ready format
        self.terminal_text.insert(tk.END, "\n" + "=" * 40 + "\n")
        self.terminal_text.insert(tk.END, "Copy-ready format:\n")
        self.terminal_text.insert(tk.END, "-" * 40 + "\n")

        # coordinate list
        coord_list = ", ".join([f"({x}, {y})" for x, y in self.points])
        self.terminal_text.insert(tk.END, f"Coordinates: {coord_list}\n\n")

    def copy_coordinates(self):
        """Copy coordinates to clipboard in simple format."""
        if not self.points:
            messagebox.showwarning(
                "No Points", "No points to copy. Place some points first."
            )
            return

        coord_list = ", ".join([f"({x}, {y})" for x, y in self.points])
        pyperclip.copy(coord_list)
        self.status_var.set("Coordinates copied to clipboard!")


def main():
    """Main function to run the application."""
    # Create main window
    main_window = tk.Tk()
    PointTraceEditor(main_window)
    # Start the main event loop
    main_window.mainloop()


if __name__ == "__main__":
    main()
