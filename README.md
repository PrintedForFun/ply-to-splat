# Ply to Gaussian Splat

CloudCompare.exe -O "C:\Users\phili\Downloads\Basement.ply" -SS SPATIAL 0.01

````
"%PROGRAMFILES%\CloudCompare\CloudCompare.exe" -SILENT -AUTO_SAVE OFF -O -GLOBAL_SHIFT AUTO "%USERPROFILE%\Downloads\<input>.ply" -SS SPATIAL 0.0075 -C_EXPORT_FMT PLY -SAVE_CLOUDS FILE "%USERPROFILE%\Downloads\<output>.ply"
````

# Running supersplat editor
Clone repo
`npm run serve`
Open url, edit spalt, export as .sog

# Opening scan in supersplat
`npm run serve`
place 