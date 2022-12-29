# epJSON Editor

epJSON Editor provides a simple way of creating or editing [EnergyPlus](https://www.energyplus.net) input data files in epJSON format. It is intended to provide essentially the same functionality as IDF Editor, but as a Python program it may be used on more platforms and is easier for interested parties to contribute to. The editor does provide some degree of error checking to the extent that it does verify that some fields are valid. Some numeric fields are highlighted if the current value is out of range and some text fields are highlighted if they contain an invalid reference. For instructions and rules that must be followed when creating an EnergyPlus input file the user should refer to the Input/Output Reference document.

## Overview

epJSON Editor is written in the [Python](https://www.python.org) language and uses that the [wxPython](https://www.wxpython.org) cross-platform user interface toolkit. The program is open source and is made available under a three clause BSD license. It represents EnergyPlus input objects in a tabular style that allows users to quickly make changes to the input file. Full documentation for the program will be available in the future.

## Contributing

If you'd like to contribute, please fork the repository and use a branch. Pull requests are welcome.

Please report any bugs you find or suggestions for features [here](https://github.com/ORNL-BTRIC/epJSON-Editor/issues) using "New Issue".

## License

The code in this project is licensed under BSD-3 license.

## Links

[Main EnergyPlus repo](https://github.com/NREL/EnergyPlus)

[IDF and epJSON documentation](https://bigladdersoftware.com/epx/docs/22-2/essentials/essentials.html#idf-and-json-syntax)