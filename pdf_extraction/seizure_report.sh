PDF_PATH="$1"

if [[ -z "$PDF_PATH" ]]; then
    echo "INPUT PATH NOT SPECIFIED, usage <INPUT>"
fi


for file in $PDF_PATH/*.pdf; do
    if [ -f "$file" ]; then
        java -jar tabula-1.0.2-jar-with-dependencies.jar "$file" -a 161.865,14.985,555.015,715.925 -p 1 >> "${file%.pdf}_1.csv"
		java -jar tabula-1.0.2-jar-with-dependencies.jar "$file" -a 136.125,15.995,272.845,715.925 -p 2 >> "${file%.pdf}_2.csv"
    fi
done