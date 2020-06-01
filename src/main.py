import ctypes
import sys

import PySimpleGUI as sg

import comparison_utils

# Needed if using tkinter on win10 HiDPI screen because of font blurring
if 'win' in sys.platform:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

sg.theme("Light Blue 2")
col_radios = [[sg.Radio("Difference: B - A", "RADIO1", key="B-A", default=True,
                        tooltip="The set of items in B that aren't in A.")],
              [sg.Radio("Difference: A - B", "RADIO1", key="A-B", tooltip="The set of items in A that aren't in B.")],
              [sg.Radio("Union: A ⋃ B", "RADIO1", key="AUB", tooltip="The set of all items in A and B.")],
              [sg.Radio("Symmetric Difference: A ∆ B", "RADIO1", key="A^B",
                        tooltip="The set of items that are in either A or B, but not both.")],
              [sg.Radio("Intersection: A ⋂ B", "RADIO1", key="A⋂B",
                        tooltip="The set of items that are shared between A and B.")]]
col_A = [[sg.Text("Original Search File (A):")],
         [sg.Input(key="A"),
          sg.FileBrowse(file_types=([("csv or xml File", "*.csv;*.xml")]))],
         [sg.Frame("Select Set Operation for Comparison:",
                   [[sg.Column(col_radios)]])]
         ]
col_B = [[sg.Text("New Search File (B):")],
         [sg.Input(key="B"),
          sg.FileBrowse(file_types=([("csv or xml File", "*.csv;*.xml")]))],
         [sg.Frame("Summary:", [[sg.Text(key="-SUMMARY-", size=(30, 7))]])]
         ]

layout = [
    [sg.Text("Enter 2 files to compare", justification="center", font="Helvetica 15")],
    [sg.Column(col_A), sg.VerticalSeparator(), sg.Column(col_B)],
    [sg.Button("Compare", tooltip="Perform set operations to compare file A and file B")],
    [sg.Text("Results:")],
    [
        sg.Table(
            values=[[" " * 84]],
            headings=["Title"],
            background_color="lightyellow",
            display_row_numbers=True,
            max_col_width=20000,
            justification="left",
            num_rows=10,
            alternating_row_color="lightblue",
            key="-TABLE-",
            tooltip="Resulting Titles Determined by Selected Set Operation",
        )
    ],
    [sg.Text("Warnings:")],
    [sg.Output(key="-OUTPUT-", text_color="red", size=(106, 6))],
    [
        sg.SaveAs(
            file_types=([("csv File", "*.csv")]), change_submits=True
        ),
    ],
    [sg.Exit()],
]


def get_radio_operation(values):
    radio_keys = ['A-B', 'B-A', 'AUB', 'A^B', 'A⋂B']
    for k in radio_keys:
        if values[k]:
            return k


window = sg.Window("Our2D2", layout, auto_size_buttons=True, auto_size_text=True, icon='../assets/icon.ico',
                   location=(0, 0), resizable=True)
title_lists = []
results = set()
while True:
    event, values = window.read()
    if event in (None, "Exit"):
        break
    if event == "Compare" and values['A'] != "" and values['B'] != "":
        window["-OUTPUT-"].update("")  # Clear error output
        title_lists = comparison_utils.create_title_lists(values["A"], values["B"])
        if len(title_lists) != 2:
            continue
        results, summary_str = comparison_utils.summary_stats(
            title_lists[0], title_lists[1], get_radio_operation(values)
        )
        window["-SUMMARY-"].update(summary_str)
        window["-TABLE-"].update(values=[[record.title] for record in results])

    if event == "Save As...":
        file_path = values["Save As..."]
        if not file_path.endswith('.csv'):
            file_path += '.csv'
        comparison_utils.save_csv(file_path, results)

window.close()
