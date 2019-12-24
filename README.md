# Fast and Dirty Manga translation tool

This tool is a very first and dirty tool to translate manga.

It was written in a couple of hours but proved useful to speed up the process
of cleaning and typesetting. As it is you can't expect good results from it,
but if you need to translate several chapters in minutes starting from
zero it makes the cleaning and writing translated text a very fast process,
making it possible to have a complete volume ready in a matter of hours.

The output quality is terrible, and I wouldn't recommend using this for
any definitive version. Don't expect the output to look professional at
all.

The typesetting is limitted to just "two fonts", a "big" font and a "small"
font. Those are hardcoded as it is now but they could be changed easily
in the source code.

## Dependencies

This software requires Python 3.5+ and the following libraries:
- pygame
- patool

## Base concepts

This software allows to create a new "Project" based on a given CBZ/CBR/ZIP/RAR file.

New "Projects" can be edited/translated, the output is saved every time the page changes.

When translation/edition is complete, the edited "Project" can be exported as a CBZ/CBR/ZIP/RAR file.

## Command line

### Creating a new project

To create a new project based on an input cbr file, use the following command:

`mangatr -i <file.cbr> - p <project folder>`

The <project folder> must not previously exist, it will be created but the software.

### Exporting an edited project

To export an edited project to a given output cbr file, use the following command:

`mangatr -o <file.cbr> - p <project folder>`

### Editing a project

To edit a project use the following command line:

`mangatr -e - p <project folder>`

## Editing

### Browsing

The software allows to browse along different pages on the project, for
this the user should use the following keyboard inputs:

|   Key   |    Function     |
|:-------:|:---------------:|
| TAB      | Switch beween original page and edit mode |
| Keypad + | Zoom in |
| Keypad - | Zoom out |
| Arrows   | Pan around the page |
| W        | Change to previous page |
| E        | Change to next page |
| ESC      | Press three times in a row to exit |


### Edit Mode

The software provides 4 modes:
- Polygon clean mode ("R" mode)
- Box clean mode ("F" mode)
- Text entry mode ("T" mode)

The following keys are used in edit mode:

| Key  | Function |
|:----:|:--------:|
| R    | Enter polygon clean mode. If already in polygon clean mode, remove all polygon edges. |
| T    | Enter text entry mode. If already in text entry mode, change to the next typesetting preset. |
| F    | Enter box clean mode |
| I    | Switch background/foreground color for all following operations |

#### Polygon clean mode ("R" mode)

In this mode the user can clean an area defined by a polygon, filling the polygon with the current background color.

The polygon clean mode is operated with the mouse:
- Edges are added to the polygon by left clicking over the page. 
- The last added edge can be removed from the polygon by middle clicking anywhere.
- The area defined by the polygon is cleaned to the background color by right clicking anywhere.

#### Box clean mode ("F" mode)

In this mode the user can clean an area defined by a rectangle. The rectangle background will
be filled with the current background color. The rectangle will have a one pixel border defined
by the current foreground color.

The box clean mode is operated with the mouse:
- Left click to define the top-left corner of the rectangle
- Right click to define the bottom-right corner of the rectangle
- Middle click to apply the rectangle to the page

#### Text entry mode ("T" mode)

In text entry mode text can be entered in the position clicked.
First enter text entry mode by pressing the "T" key, then click
where text shall be entered.

When text is being entered all key commands are ignored, except for
the TAB key used for switching between original and edited view.

To exit text entry mode **without** aplying changes press the ESC key.

To exit text entry mode **aplying changes** right click anywhere.

