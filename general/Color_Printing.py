'''
Color formating for the 'print' method
'''

class ColorFormat:
    green = "\033[92m"
    yellow = "\033[93m"
    cyan = "\033[36m"
    magenta = "\033[35m"
    end = "\033[0m\n"

    @staticmethod
    def printColor(itext, color="c"):
        if "c" in color:
            print( ColorFormat.cyan + str(itext) + ColorFormat.end)
        elif "g" in color:
            print( ColorFormat.green + str(itext) + ColorFormat.end)
        elif "m" in color:
            print( ColorFormat.magenta + str(itext) + ColorFormat.end)
        elif "y" in color:
            print( ColorFormat.yellow + str(itext) + ColorFormat.end)
        else:
            print(itext)
