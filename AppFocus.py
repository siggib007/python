import win32gui, win32console, win32event, ctypes, subprocess, win32con, time
import win32com.client as win32
user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.LockSetForegroundWindow(1)
# p = subprocess.Popen('notepad')
print ("starting word")
app = win32.gencache.EnsureDispatch('word.Application')
app.Visible = True
strDocName = "C:/Users/sbjarna/Downloads/access_port_automation.doc"
Docin = app.Documents.Open(strDocName)

# print ("waiting 5 sec then attempt to give the focus back to here")
# # win32event.WaitForInputIdle(app._handle, 1000)
# time.sleep(5)
# win32gui.SetWindowPos(win32console.GetConsoleWindow(), win32con.HWND_TOP, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)