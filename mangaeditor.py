import pygame
import pygame.gfxdraw
import sys
import threading
import ctypes
import platform
import glob
import os

filesBeingSaved = {}

def windowsFix():
    # Query DPI Awareness (Windows 10 and 8)
    awareness = ctypes.c_int()
    errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))

    # Set DPI Awareness  (Windows 10 and 8)
    errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)
    # the argument is the awareness level, which can be 0, 1 or 2:
    # for 1-to-1 pixel control I seem to need it to be non-zero (I'm using level 2)

    # Set DPI Awareness  (Windows 7 and Vista)
    success = ctypes.windll.user32.SetProcessDPIAware()
    # behaviour on later OSes is undefined, although when I run it on my Windows 10 machine, it seems to work with effects identical to SetProcessDpiAwareness(1)

def blit_text_cr(surface, text, pos, font, color=pygame.Color('black')):
    space = font.size(' ')[0]  # The width of a space.
    max_width, max_height = surface.get_size()
    x, y = pos
    for line in text.splitlines():
        line_surface = font.render(line, True, color)
        line_width, line_height = line_surface.get_size()
        
        surface.blit(line_surface, (x, y))
        
        y += round(line_height*.9)  # Start on new row.
        
def comicStyleBoxDel(surface, rect, bgcolor=pygame.Color('black'), bordercolor=pygame.Color('white')):
    # Draw background
    pygame.gfxdraw.box(surface, rect, bgcolor)
    # Draw border
    pygame.gfxdraw.rectangle(surface, rect, bordercolor)
    
class MangaEditor:
    def __init__(self, projectFolder):
        self._project = projectFolder
        self._createFileList()
        
    def start(self):
        if platform.system() == 'Windows':
            windowsFix()
            
        # Consider this the main thread that will read events
        # Initialize pygame
        pygame.init()
        screen = pygame.display.set_mode( (0,0) , flags = pygame.FULLSCREEN | pygame.HWSURFACE)
        
        # Create additional thread for handling events
        eventHandler = MangaEventHandler(screen, self)
        
        while eventHandler.handleEvent( pygame.event.wait() ):
            pass
            
    def _createFileList(self):
        baseDir = self._project + '/orig/'
        
        fileListJpg = glob.glob(baseDir + '**/*.jpg', recursive=True)
        fileListPng = glob.glob(baseDir + '**/*.png', recursive=True)
        
        self._fileList = fileListJpg + fileListPng
        
        self._fileList = [os.path.splitext(a)[0][len(baseDir):] for a in self._fileList]
        
        self._fileList.sort()
        
    def getFileList(self):
        return self._fileList
        
    def getProjectFolder(self):
        return self._project
        

class MangaEventHandler:
    def __init__(self, displaySurface, mangaEditorInstance):
        self._screen = displaySurface
        self._mangaEditor = mangaEditorInstance
        self._original = True
        self._zoom = 1.0
        self._sw, self._sh = displaySurface.get_size()
        self._fonts = MangaFonts()
        self._erasePoly = []
        self._mode = 0
        self._unsavedChanges = False
        self._escapeCount = 0
        self._text = ""
        self._textPos = (0, 0)
        self._fontType = 0
        self._invertColors = False
        self._boxDelCoord = [None, None]
        
        self._changePage(0)
        
    def _black(self):
        if self._invertColors:
            return (255, 255, 255)
        else:
            return (0, 0, 0)

    def _white(self):
        if self._invertColors:
            return (0, 0, 0)
        else:
            return (255, 255, 255)
            
    def handleEvent(self, event):
        if event.type == pygame.QUIT:
            return False
            
        if event.type == pygame.KEYDOWN:
            if event.key != pygame.K_ESCAPE:
                self._escapeCount = 0
                
            if self._mode != 2:
                if event.key == pygame.K_ESCAPE:
                    self._escapeCount = self._escapeCount + 1
                    if self._escapeCount >= 3:
                        if self._unsavedChanges:
                            saveThread = SavePageThread(self._mangaPage)
                            saveThread.start()
                        return False
                elif event.key == pygame.K_TAB:
                    self._original = not self._original
                    self._redraw()
                elif event.key == pygame.K_i:
                    self._invertColors = not self._invertColors
                    self._redraw()
                elif event.key == pygame.K_w:
                    self._prevPage()
                elif event.key == pygame.K_e:
                    self._nextPage()
                elif event.key == pygame.K_r:
                    if not self._original:
                        self._mode = 1
                        self._erasePoly = []
                        self._redraw()
                elif event.key == pygame.K_f:
                    if not self._original:
                        self._mode = 3
                        self._boxDelCoord = [None, None]
                        self._redraw()
                elif event.key == pygame.K_t:
                    if not self._original:
                        if self._mode == 0:
                            self._fontType += 1
                            if self._fontType > 1:
                                self._fontType = 0
                        else:
                            self._mode = 0
                        self._redraw()            
                elif event.key == pygame.K_KP_PLUS:
                    if self._zoom < 10:
                        self._zoom = self._zoom + 0.25
                        self._redraw()
                elif event.key == pygame.K_KP_MINUS:
                    if self._zoom > 0.25:
                        self._zoom = self._zoom - 0.25
                        self._redraw()
                elif event.key == pygame.K_UP:
                    self._off[1] -= 100
                    self._redraw()
                elif event.key == pygame.K_DOWN:
                    self._off[1] += 100
                    self._redraw()
                elif event.key == pygame.K_LEFT:
                    self._off[0] -= 100
                    self._redraw()
                elif event.key == pygame.K_RIGHT:
                    self._off[0] += 100
                    self._redraw()
            else:
                if event.key == pygame.K_ESCAPE:
                    self._mode = 0
                    self._text = ""
                    self._redraw()
                elif event.key == pygame.K_RETURN:
                    self._text += '\n'
                    self._redraw()
                elif event.key == pygame.K_BACKSPACE:
                    self._text = self._text[:-1]
                    self._redraw()
                elif event.key == pygame.K_TAB:
                    self._original = not self._original
                    self._redraw()
                else:
                    self._text += event.unicode
                    self._redraw()                
                    
        if event.type == pygame.MOUSEBUTTONDOWN:            
            if self._mode == 1 and not self._original:
                if event.button == 1:
                    self._erasePoly.append(self._mapScr2Page(event.pos))
                    self._redraw()
                if event.button == 3 and len(self._erasePoly) >= 3:
                    self._applyErasePoly()
                    self._erasePoly = []
                    self._redraw()
                if event.button == 2 and len(self._erasePoly) > 0:
                    self._erasePoly.pop()
                    self._redraw()
            elif self._mode == 0 and not self._original:
                if event.button == 1:
                    self._textPos = self._mapScr2Page(event.pos)
                    self._text = ""
                    self._mode = 2
                    self._redraw()
            elif self._mode == 2 and not self._original:
                if event.button == 3:
                    self._applyText()
                    self._mode = 0
                    self._redraw()
            elif self._mode == 3 and not self._original:
                if event.button == 1:
                    self._insertBoxLeftDelCoord(self._mapScr2Page(event.pos))
                    self._redraw()
                elif event.button == 3:
                    self._insertBoxRightDelCoord(self._mapScr2Page(event.pos))
                    self._redraw()
                elif event.button == 2:
                    self._applyBoxDel()
                    self._mode = 0
                    self._redraw()
                    
        return True
        
    def _changePage(self, newIdx):
        saveThread = None
        
        if self._unsavedChanges:
            saveThread = SavePageThread(self._mangaPage)
            self._unsavedChanges = False
            
        newFile = self._mangaEditor.getFileList()[newIdx]
        
        busySaveThread = filesBeingSaved.get(newFile, None)
        if busySaveThread is not None:
            busySaveThread.join()
        
        self._mangaPage = MangaPage(self._mangaEditor.getProjectFolder(), newFile)
        self._pageIdx = newIdx
        self._topRecenter()
        self._redraw()

        if saveThread is not None:
            # We delay starting the save thread to the very end step
            # of change page, this way we don't saturate our precious
            # limited resource needed both for reading a new page
            # and saving the old page: HDD bandwidth.
            saveThread.start()
        
    def _topRecenter(self):
        self._off = [0, 0]
        
    def _redraw(self):
        if self._original:
            srf = self._mangaPage.getOrigSurface()
        else:
            srf = self._mangaPage.getEditSurface()
        
        srfSize = srf.get_rect()
        
        if self._mode == 2 and not self._original:
            srf = srf.copy()
            text = self._text + "|"
            
            if self._fontType == 0:
                font = self._fonts.getTitleFont()
            else:
                font = self._fonts.getDialogFont()
            blit_text_cr(srf, text, self._textPos, font, self._black())
        elif self._mode == 3 and not self._original:
            if self._boxDelCoord[0] is not None and self._boxDelCoord[1] is not None:
                srf = srf.copy()
                rect = self._getBoxDelRect()
                comicStyleBoxDel(srf, rect, self._white(), self._black())
            
            
        
        blitSurf = pygame.transform.scale(srf, (round(srfSize.w * self._zoom), round(srfSize.h * self._zoom)))
        
        rect = blitSurf.get_rect()
        
        rect = rect.move([round(self._sw - srfSize.w*self._zoom)/2 + self._off[0], round(self._sh - srfSize.h*self._zoom)/2  + self._off[1]])
        
        self._screen.fill( (0,0,0) )
        self._screen.blit(blitSurf, rect)
        
        if self._original:
            text = self._fonts.getMainFont().render("ORIGINAL", True, (0,255,0) )
            self._screen.blit(text, (0, 0) )       
        else:
            if self._mode == 1:
                text = self._fonts.getMainFont().render("{}R".format("I" if self._invertColors else ""), True, (0,255,0) )
                self._screen.blit(text, (0, 0) )       
                self._drawPartialPoly()
            elif self._mode in (0, 2):
                text = self._fonts.getMainFont().render("{}T{}".format("I" if self._invertColors else "", self._fontType), True, (0,255,0) )
                self._screen.blit(text, (0, 0) )
            elif self._mode == 3:
                text = self._fonts.getMainFont().render("{}F".format("I" if self._invertColors else ""), True, (0,255,0) )
                self._screen.blit(text, (0, 0) )

        
        pygame.display.flip()
        
    def _prevPage(self):
        self._pageIdx = self._pageIdx - 1
        if self._pageIdx < 0:
            self._pageIdx = len(self._mangaEditor.getFileList()) - 1
            
        self._changePage(self._pageIdx)
        
    def _nextPage(self):
        self._pageIdx = self._pageIdx + 1
        if self._pageIdx >= len(self._mangaEditor.getFileList()):
            self._pageIdx = 0
            
        self._changePage(self._pageIdx)
        
    def _mapScr2Page(self, pos):
        sx = pos[0]
        sy = pos[1]
        pw, ph = self._mangaPage.getEditSurface().get_size()
        
        px = round((sx - (self._sw-pw*self._zoom)/2-self._off[0]) / self._zoom)
        py = round((sy - (self._sh-ph*self._zoom)/2-self._off[1]) / self._zoom)
        
        return (px, py)
        
    def _mapPage2Scr(self, pos):
        px = pos[0]
        py = pos[1]
        pw, ph = self._mangaPage.getEditSurface().get_size()
        
        sx = round((self._sw-pw*self._zoom)/2+self._off[0] + px*self._zoom)
        sy = round((self._sh-ph*self._zoom)/2+self._off[1] + py*self._zoom)
        
        return (sx, sy)
    
    def _drawPartialPoly(self):
    
        for pIdx in range(1, len(self._erasePoly)):
            pygame.gfxdraw.line(self._screen, 
                                self._mapPage2Scr(self._erasePoly[pIdx-1])[0], 
                                self._mapPage2Scr(self._erasePoly[pIdx-1])[1], 
                                self._mapPage2Scr(self._erasePoly[pIdx])[0], 
                                self._mapPage2Scr(self._erasePoly[pIdx])[1], 
                                (255,0,0) )
                                
        for point in self._erasePoly:
            rect = pygame.Rect(self._mapPage2Scr(point)[0]-1, 
                               self._mapPage2Scr(point)[1]-1,
                               3, 3)
            pygame.gfxdraw.box(self._screen, rect, (255, 0, 0))
        
            
    def _applyErasePoly(self):
        pygame.gfxdraw.filled_polygon(self._mangaPage.getEditSurface(), 
                                      self._erasePoly, self._white())
                                      
        self._unsavedChanges = True
        
    def _applyText(self):

        if self._fontType == 0:
            font = self._fonts.getTitleFont()
        else:
            font = self._fonts.getDialogFont()
        blit_text_cr(self._mangaPage.getEditSurface(), self._text, self._textPos, font, self._black())
        self._unsavedChanges = True
        
    def _getBoxDelRect(self):
        # Find out leftest
        left = min(self._boxDelCoord[0][0], self._boxDelCoord[1][0])
        right = max(self._boxDelCoord[0][0], self._boxDelCoord[1][0])
        top = min(self._boxDelCoord[0][1], self._boxDelCoord[1][1])
        bottom = max(self._boxDelCoord[0][1], self._boxDelCoord[1][1])
        w = right - left
        h = bottom - top
        return pygame.Rect(left, top, w, h)
        
    def _applyBoxDel(self):
        if self._boxDelCoord[0] is not None and self._boxDelCoord[1] is not None:
            rect = self._getBoxDelRect()
            comicStyleBoxDel(self._mangaPage.getEditSurface(), rect, self._white(), self._black())
            self._unsavedChanges = True
        
    def _insertBoxLeftDelCoord(self, pos):
        if self._boxDelCoord[1] is None:
            self._boxDelCoord[0] = pos
            self._boxDelCoord[1] = pos
        else:
            if self._boxDelCoord[1][0] > pos[0] and self._boxDelCoord[1][1] > pos[1]:
                self._boxDelCoord[0] = pos
                
    def _insertBoxRightDelCoord(self, pos):
        if self._boxDelCoord[0] is None:
            self._boxDelCoord[0] = pos
            self._boxDelCoord[1] = pos
        else:
            if self._boxDelCoord[0][0] < pos[0] and self._boxDelCoord[0][1] < pos[1]:
                self._boxDelCoord[1] = pos
        
        
    
class MangaPage:
    def __init__(self, projectFolder, baseFileName):
        self._baseFileName = baseFileName
        self._project = projectFolder
        self._origSurface = None
        self._editSurface = None
        
        # create orig/edit surfaces
        self._origSurface = self._loadImg(projectFolder + '/orig/' + baseFileName)
        self._editSurface = self._loadImg(projectFolder + '/edit/' + baseFileName)
        
    def getBaseFileName(self):
        return self._baseFileName
        
    def getOrigSurface(self):
        return self._origSurface
        
    def getEditSurface(self):
        return self._editSurface
        
    def getProjectFolder(self):
        return self._project
        
    def _loadImg(self, imgName):
        if os.path.exists(imgName + '.png'):
            return pygame.image.load(imgName + '.png')
        else:
            return pygame.image.load(imgName + '.jpg')
        

class SavePageThread(threading.Thread):
    def __init__(self, mangaPage, group=None, target=None, name=None):
                 
        super().__init__(group=group, target=target, 
			              name=name)
                          
        self._mangaPage = mangaPage
        self._surface = mangaPage.getEditSurface()
        
    def run(self):
        baseFileName = self._mangaPage.getBaseFileName()
        projectFolder = self._mangaPage.getProjectFolder()
        
        # Put base file name in filesBeingSaved
        filesBeingSaved[baseFileName] = self
        # Save PNG file
        outputName = projectFolder + '/edit/' + baseFileName + '.png'
        pygame.image.save(self._surface, outputName)
        # If JPG file exists delete it
        deleteName = projectFolder + '/edit/' + baseFileName + '.jpg'
        if os.path.exists(deleteName):
            os.remove(deleteName)
        # Remove base file name from filesBeingSaved
        filesBeingSaved.pop(baseFileName)
        

class MangaFonts:
    def __init__(self):
        self._mainFont = pygame.font.SysFont("comicsansms", 72)
        self._titleFont = pygame.font.SysFont("comicsansms", 30, bold=True)
        self._dialogFont = pygame.font.SysFont("comicsansms", 22, bold=True)
        
    def getMainFont(self):
        return self._mainFont

    def getTitleFont(self):
        return self._titleFont

    def getDialogFont(self):
        return self._dialogFont

