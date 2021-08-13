import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import button_color_to_tuple
import random
import string
import os
from pathlib import Path
import re

class Interface:
    title_font = ("Arial", 30)
    text_font = ("Consolas", 18)
    label_font = ("Consolas", 13)
    characters_wide = 100
    colors = ['blue', 'indigo', 'pink', 'violet','green',  'brown', 'orange',  'turquoise']
    random.shuffle(colors)

    def __init__(self, target_text):
        self.target_text = target_text
        self.current_label = 0
        self.previous_label = 0
        self.create_layout()
        self.handle_events()

    def create_layout(self):
        self.generate_annotation_buttons()
        self.textbox = sg.Multiline(  default_text = self.target_text.text, key='_OUT_', font = Interface.text_font, 
                                        size=(Interface.characters_wide, 2 + self.target_text.get_length() // Interface.characters_wide))
        self.new_entity_entry = sg.InputText(font=Interface.text_font)
        self.layout = [ [sg.Text("Annotate the following text:", font = Interface.title_font)],
                        self.annotation_buttons,
                        [sg.Text('Add another entity:', font = Interface.text_font), self.new_entity_entry, sg.Button('Add', font = Interface.text_font)],
                        [self.textbox],
                        [sg.Button('Annotate', font = Interface.text_font), sg.Button('Submit', font = Interface.text_font)]]
        self.window = sg.Window('NER Annotation Tool').Layout(self.layout).Finalize()
        self.window.Element('_OUT_').bind("<FocusIn>", '+FOCUS_IN+')
        self.window.Element('_OUT_').bind("<FocusOut>", '+FOCUS_OUT+')
        self.update_text()

    def generate_annotation_buttons(self):
        labels = self.target_text.labels
        self.annotation_buttons = []
        self.index_to_color = {}
        for i, label in enumerate(labels):
            if i < len(Interface.colors): color = Interface.colors[i]
            else: color = "grey"
            self.index_to_color[i] = ("white", color)
            font = Interface.text_font
            if i == self.current_label: 
                additional = '✓'
            else:
                additional = ' '
            if label == "REMOVE":
                color = ("red", "white")
                self.index_to_color[i] = color
            button = sg.Button(additional + label, font = font,  button_color = color)
            self.annotation_buttons.append(button)
        for i in range(8-len(labels)):
            button = sg.Button('', font = font,  button_color = color, visible = False)
            self.annotation_buttons.insert(-1,button)

    def handle_events(self):
        while True:
            event, values = self.window.read()
            if event == sg.WINDOW_CLOSED:
                exit()
            elif event[1:] in self.target_text.labels:
                self.update_annotation_buttons(event[1:])
            elif event == "Add":
                self.add_entity(values[0])
            elif event == "Annotate":
                try:
                    start = int(self.textbox.Widget.index("sel.first")[2:])
                    end = int(self.textbox.Widget.index("sel.last")[2:])
                    text = self.textbox.Widget.selection_get()
                    if len(set(list(text)) & (set(list(string.punctuation)) | {' '})) != len(set(list(text))) and self.textbox.Widget.index("sel.last") != '2.0':
                        self.handle_annotation(start, end)
                except:
                    pass
            elif event == "Submit":
                self.target_text.produce_xml()
                exit()
            elif event == '_OUT_+FOCUS_IN+':
                widget = self.window['_OUT_'].Widget
                widget.bind("<1>", widget.focus_set())
                self.window['_OUT_'].update(disabled=True)
            elif event == '_OUT_+FOCUS_OUT+':
                self.window['_OUT_'].Widget.unbind("<1>")
                self.window['_OUT_'].update(disabled=False)  

    def add_entity(self, label):
        label = label.upper()
        if len(label) > 0 and label not in self.target_text.labels:
            self.target_text.labels.insert(-1, label)
            self.window.Close()
            self.create_layout()

    def handle_annotation(self, start, end):
        if self.target_text.labels[self.current_label] != 'REMOVE':
            real_start = self.target_text.get_word_start(start)
            real_end = self.target_text.get_word_end(end)
            self.target_text.add_annotation(real_start, real_end, self.current_label)
        else:
            self.target_text.remove_annotations(start, end)
        self.update_text()

    def update_text(self):
        annotations = self.target_text.annotations
        full_text = self.target_text.text
        if len(annotations) > 0:
            initial_start = annotations[0][0]
        else:
            initial_start = len(full_text)
        initial_text = full_text[:initial_start]
        self.textbox.Update(initial_text)
        for index, chunk in enumerate(annotations):
            start = chunk[0]
            end = chunk[1]
            label = chunk[2]
            text_chunk = full_text[start:end]
            bg_color = self.index_to_color[label][1]
            text_color = self.index_to_color[label][0]
            self.textbox.Update(text_chunk, append = True, background_color_for_value = bg_color, text_color_for_value = text_color)
            if index == len(annotations) - 1:
                next_start = len(full_text)
            else:
                next_start = annotations[index + 1][0]
            self.textbox.Update(full_text[end:next_start], append = True)

    def update_annotation_buttons(self, new):
        self.previous_label = self.current_label
        self.current_label = self.target_text.labels.index(new)
        self.annotation_buttons[self.previous_label].Update(' ' + self.target_text.labels[self.previous_label])
        self.annotation_buttons[self.current_label].Update('✓' + self.target_text.labels[self.current_label])

class AnnotatedText:
    def __init__(self, input_path = "testing_data.xml", output_path = "annotated.xml", paragraph_number = -1):
        self.input_path = input_path
        self.output_path = output_path
        self.paragraph_number = paragraph_number
        self.parse_input_xml()
        self.labels.append('REMOVE')

    def parse_input_xml(self):
        annotated_text = open(self.input_path).read().split('\n')[self.paragraph_number]
        self.text = re.sub('<[^<]+?>', '', annotated_text)
        self.labels = []
        self.annotations = []
        offset = 0
        active = False
        while '<'  in annotated_text:
            start = annotated_text.index('<')
            end = annotated_text.index('>')
            if not active:
                active = True
                annotated_text = annotated_text[end+1:]
                offset += start
            else:
                real_start = offset
                real_end = offset + start
                kind = annotated_text[start+2:end].upper()
                annotated_text = annotated_text[end+1:]
                active = False
                offset += start
                if kind not in self.labels:
                    self.labels.append(kind)
                self.annotations.append([real_start, real_end, self.labels.index(kind), kind])
        
    #dealing with cases to handle annotations & overlaps
    def add_annotation(self, start, end, label_index):
        label = self.labels[label_index]
        start_pos = 0

        if len(self.annotations) == 0:
            self.annotations.append([start, end, label_index, label])

        else:
            while self.annotations[start_pos][0] < start: 
                start_pos += 1
                if start_pos == len(self.annotations): break
            
            if start_pos == len(self.annotations):
                if self.annotations[start_pos-1][1] > start:
                    self.annotations[start_pos-1] = [start, end, label_index, label]
                else:
                    self.annotations.append([start, end, label_index, label])

            elif start > self.annotations[start_pos -1][1] and end <  self.annotations[start_pos][0] and start_pos != 0:
                self.annotations.insert(start_pos, [start, end, label_index, label])

            else:
                if start_pos == 0 and end < self.annotations[start_pos][0]:
                    self.annotations.insert(start_pos, [start, end, label_index, label])
                else:
                    if start_pos != 0 and start >= self.annotations[start_pos - 1][0] and start <= self.annotations[start_pos - 1][1]:
                        self.annotations.pop(start_pos - 1)
                        start_pos -= 1
                    while self.annotations[start_pos][0] < end:
                        self.annotations.pop(start_pos)
                        if len(self.annotations) == 0: break
                        if start_pos == len(self.annotations): break
                    if len(self.annotations) == 0: self.annotations.append([start, end, label_index, label])
                    elif start_pos == len(self.annotations): self.annotations.append([start, end, label_index, label])
                    else: self.annotations.insert(start_pos, [start, end, label_index, label])
    
    def remove_annotations(self, start, end):
        new_annotations = []
        for annotation in self.annotations:
            if (annotation[0] < end and annotation[0] > start) or (annotation[1] < end and annotation[1] > start) or (start > annotation[0] and end < annotation[1]):
                continue
            else:
                new_annotations.append(annotation)
        self.annotations = new_annotations

    def get_length(self):
        return len(self.text)

    def get_word_start(self, pos):
        while pos >= 0 and self.text[pos] != ' ':
            pos -= 1
        return pos + 1

    def get_word_end(self, pos):
        while pos < len(self.text)  and self.text[pos % len(self.text)] != ' ':
            pos += 1
        return pos

    def produce_xml(self):
        output_string = ''
        annotations = self.annotations
        full_text = self.text
        if len(annotations) > 0:
            initial_start = annotations[0][0]
        else:
            initial_start = len(full_text)
        initial_text = full_text[:initial_start]
        output_string += initial_text
        for index, chunk in enumerate(annotations):
            start = chunk[0]
            end = chunk[1]
            name = chunk[3].lower()
            text_chunk = full_text[start:end]
            output_string += f'<{name}>'
            output_string += text_chunk
            output_string += f'</{name}>'
            if index == len(annotations) - 1:
                next_start = len(full_text)
            else:
                next_start = annotations[index + 1][0]
            output_string += full_text[end:next_start]
        with open(self.output_path, "w") as f:
            f.write(output_string)

if __name__ == "__main__":
    current_directory = str(Path(os.path.realpath(__file__)[:]).parent.absolute()) + '/'
    input = current_directory + 'annotated.xml'
    output = current_directory + 'annotated.xml'
    target_text = AnnotatedText(input, output)
    Interface(target_text)