#!env python

import patoolib
import sys
import argparse
import os
import mangaeditor

def get_arg_parser():
    parser = argparse.ArgumentParser(description='Manga Translation Helper')
    parser.add_argument('-i', '--input', help='input file (CBR/CBZ) to generate project')
    parser.add_argument('-o', '--output', help='output file (CBR/CBZ) generated from project')
    parser.add_argument('-e', '--edit', action='store_true', help='edit the manga in project folder')
    parser.add_argument('-p', '--project', help='project folder')
    return parser



parser = get_arg_parser()
args = parser.parse_args()

if args.input is not None:
    #process Input
    if args.project is None:
        print("A project folder is required")
    else:
        if os.path.isdir(args.project):
            print("The project folder already exists")
        else:
            os.mkdir(args.project)
            os.mkdir(args.project+'/orig')
            os.mkdir(args.project+'/edit')
            patoolib.extract_archive(args.input, outdir=args.project+'/orig')
            patoolib.extract_archive(args.input, outdir=args.project+'/edit')

elif args.output is not None:
    #generate Output
    if args.project is None or not os.path.isdir(args.project):
        print("Invalid project folder")
    elif os.path.exists(args.output):
        print("The output file already exists")
    else:
        patoolib.create_archive(args.output, (args.project+'/edit', ))
    
elif args.edit is True:
    if args.project is None or not os.path.isdir(args.project):
        print("Invalid project folder")
    else:
        editor = mangaeditor.MangaEditor(args.project)
        editor.start()
    
else:
    parser.print_help()


