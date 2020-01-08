# IPython needs parso w/ grammar data (#3901)
# IPython autocompletion has a crash from within parso

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('parso')
