#!/usr/bin/python
import sys
import os
import json

import pygame

from lib import easygui
import common
import genmap
import graphics



class Main(object):
    """Contains the core functions that manage the flow of the program."""
    def __init__(self):
        # Initialize the pygame library
        pygame.init()
        # Initialize the object used for data used by multiple objects
        self.common = common.Common()
        # Create an instance of the event handler
        self.EventHandler = Events(self.common)
        # Determine the root directory of the program
        self.common.root_dir = os.path.dirname(os.path.dirname(__file__))
        self.common.saved_maps_dir = os.path.join(self.common.root_dir, "savedmaps")
        # Create the saved maps directory if needed
        if not os.path.exists(self.common.saved_maps_dir):
            try:
                os.mkdir(self.common.saved_maps_dir)
            except Exception:
                self.EventHandler.FatalExternalError("An error has occurred while trying to create the 'savedmaps' folder.")


    def start(self):
        """Runs whenever the program is first started/reset."""
        # Display the main menu until told to go into the edit phase
        while not self.common.edit_phase:
            self.EventHandler.main_menu()
        # Go to the edit phase
        self.edit()


    def edit(self):
        """The phase of generation where the user can see the map and
        tweak the results.
        """
        while self.common.edit_phase:
            # Update the display window
            self.EventHandler.update_display()
            # Do pygame queue events
            self.EventHandler.do_pygame_events()
        # Terminate the program
        self.EventHandler.quit()



# Pygame Event Reference #
        # QUIT             none
        # ACTIVEEVENT      gain, state
        # KEYDOWN          unicode, key, mod
        # KEYUP            key, mod
        # MOUSEMOTION      pos, rel, buttons
        # MOUSEBUTTONUP    pos, button
        # MOUSEBUTTONDOWN  pos, button
        # JOYAXISMOTION    joy, axis, value
        # JOYBALLMOTION    joy, ball, rel
        # JOYHATMOTION     joy, hat, value
        # JOYBUTTONUP      joy, button
        # JOYBUTTONDOWN    joy, button
        # VIDEORESIZE      size, w, h
        # VIDEOEXPOSE      none
        # USEREVENT        code
class Events(object):
    """Handles some generic actions as well as pygame library events."""
    # Instance of the map generator
    MapGen = None


    def __init__(self, common_inst):
        # Local reference to shared data object instance
        self.common = common_inst
        # Create graphics handling object
        self.GFX = graphics.Graphics(self.common)
        # Block certain events from cluttering up the event queue
        events_to_block = [
        pygame.JOYAXISMOTION,
        pygame.JOYBALLMOTION,
        pygame.JOYHATMOTION,
        pygame.JOYBUTTONUP,
        pygame.JOYBUTTONDOWN
        ]
        pygame.event.set_blocked(events_to_block)


    def main_menu(self):
        """The main menu that contains actions like new map and loading."""
        # Ask if the user wants to load a map or create a new one
        prompt = "Welcome to GenEditor for Tile Maps!"
        title = "Main Menu"
        options = ["New Map", "Load Map"]
        # Separate options for start up and other phases
        if self.common.edit_phase:
            options.append("Close Menu")
        else:
            options.append("Quit")
        # Display the window/prompt and get the user decision
        decision = easygui.buttonbox(prompt, title, options)
        # User wants to make a new map
        if decision == "New Map":
            self.new_map()
        # User wants to load a map
        elif decision == "Load Map":
            self.load_map()
        # Close the menu
        elif decision == "Close Menu":
            return
        # Quit the program
        elif decision == "Quit":
            self.quit()
        # Quit if response is not one of the known options
        else:
            self.quit()


    def new_map(self):
        """Sets up the map generator if needed and generates a new map."""
        # First time a map is generated
        if self.MapGen is None:
            # Parts of the prompt window
            info = "These settings can be adjusted later."
            title = "New Map"
            # Get generator parameters
            params = self.gen_param_prompt(info, title)
            # Return to start if user canceled prompt
            if params is None:
                return
            # Create map generator object
            self.MapGen = genmap.MapGenerator(self.common, params)
        else:
            # Parts of the prompt window
            info = "Change any parameters to desired values."
            title = "New Map"
            # Set default field values to current map values
            defaults = [self.MapGen.params['width'], self.MapGen.params['height'], self.MapGen.params['seed']]
            # Get generation parameters
            params = self.gen_param_prompt(info, title, defaults)
            # Return to start if user canceled prompt
            if params is None:
                return
            # Change parameters
            self.MapGen.set_params(params)
        # Generate map
        self.MapGen.gen_map()
        # Tells main to go into the edit phase
        self.common.edit_phase = True


    def gen_param_prompt(self, msg="Fill in fields", title="Prompt", defaults=[]):
        """Prompts the user to enter various map generation parameters, and returns
        them as a dictionary.
        """
        # Add generic info to end of the message displayed in the prompt window
        msg += "  Leave seed blank for a random seed."
        # Fields in the prompt
        fields = ("Width", "Height", "Seed")
        # Prompt user for data
        values = easygui.multenterbox(msg, title, fields, defaults)
        # Check if user canceled/closed the prompt
        if values is None:
            return None
        # Creat dictionary, change strings to other types as needed
        params = {
        'width' : int(values[0]),
        'height' : int(values[1]),
        'seed': values[2]
        }
        # If seed field was left empty, set seed to none to indicate random seed selection
        if params['seed'] == '':
            params['seed'] = None
        return params


    def load_map(self):
        """Loads a map from a JSON-formatted file."""
        # Prompt user for the map file to open
        map_file = easygui.fileopenbox("Select the map file to open.")
        # Stop and return to start if user canceled/closed the window
        if map_file == None:
            return
        # Open the file and process the JSON data
        with open(map_file, 'r') as f:
            json_data = None
            try:
                # Load file's JSON data into python objects
                json_data = json.loads(f.read())
                # Load tile map
                self.common.tile_map = json_data['tile_map']
                # Create generator with the loaded map's parameters
                self.MapGen = genmap.MapGenerator(self.common, json_data['generator_data'])
                # Switch to map edit phase
                self.common.edit_phase = True
            # JSON could not load data from the file or it is not correctly formatted
            except (ValueError, KeyError):
                # Display info to user
                msg = "\"{name}\" is not a valid GenEditor JSON formatted map file.".format(
                    name=os.path.basename(map_file)
                    )
                easygui.msgbox(msg, "Invalid Map")
            finally:
                # Clear JSON data to save memory
                del json_data


    def save_map(self):
        """Writes the map data to a text file and image file."""
        # Prompt for the save location
        save_path = easygui.filesavebox("Two files will be created, one image and one text file.")
        # User cancels the save operation
        if save_path is None:
            return
        # Get a complete rendering of the map
        img = self.GFX.render_full_map()
        # Check if that is already a file(s) with that name(s), and if it ok to override it
        msg = "There is already a file in this location with that name.  Override?"
        if (os.path.exists(save_path+".bmp") or os.path.exists(save_path+".json")) and easygui.buttonbox(msg, "Continue?", ("Yes", "No")) == "No":
            return
        # Otherwise save the map files
        else:
            # Save image to file
            pygame.image.save(img, save_path + ".bmp")
            # Save map data as JSON data
            with open(save_path + ".json", 'w') as f:
                data = {'generator_data' : self.MapGen.params, 'tile_map' : self.common.tile_map}
                # how does the user feel about indentation?
                spaces = easygui.buttonbox("Should I prettyprint the JSON results?", "prettyprint?", ("Yes", "No")) == "Yes" and 4 or 0
                if spaces != 0:
                    json.dump(data, f, indent=spaces)
                else:
                    json.dump(data, f)
            # Indicate saving is complete
            easygui.msgbox("\"" + str(os.path.basename(save_path)) + "\" saved successfully", "Save Complete")


    def do_pygame_events(self):
        """Processes events from the pygame event queue."""
        # Get a list of events, the first one allows the program to idle when not in use
        events = [pygame.event.wait()] + pygame.event.get()
        for event in events:
            # Quit program event (e.g. close window, etc.)
            if event.type == pygame.QUIT:
                self.common.edit_phase = False
                break
            # Event processing for during the edit phase
            elif self.common.edit_phase:
                self.do_pygame_edit_phase_event(event)
            # Other situations
            else:
                pass


    def do_pygame_edit_phase_event(self, event):
        """Processes reactions to pygame events for the edit phase."""
        # Keyboard release
        if event.type == pygame.KEYUP:
            # Opens the main menu
            if event.key == pygame.K_ESCAPE:
                self.main_menu()
        # Keyboard press
        elif event.type == pygame.KEYDOWN:
            # Get the current keyboard key states
            key_states = pygame.key.get_pressed()
            # Save the current map (CTRL+S)
            if key_states[pygame.K_s] and (key_states[pygame.K_LCTRL] or key_states[pygame.K_RCTRL]):
                self.save_map()


    def update_display(self):
        """Updates the display window."""
        self.GFX.render_display()


    def unimplemented_feature(self):
        """Indicates to the user that a feature they tried to use hasn't been
        implemented yet.
        """
        # Display message box
        easygui.msgbox("That Feature is not yet available.", "Sorry!")


    def FatalExternalError(self, msg=""):
        """Used to terminate the program with a message when a serious issue occurs.
        This includes file/directory permission issues, etc.
        """
        print msg
        # Display message
        easygui.msgbox(str(msg)+"  The program will now be terminated.",
            "A Fatal External Error Has Occurred")
        self.quit()


    def quit(self):
        """Does any cleanup operations then terminates the program."""
        # Terminate pygame functions
        pygame.quit()
        sys.exit()



M = Main()
M.start()
