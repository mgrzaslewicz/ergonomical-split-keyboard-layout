LAYOUT_FILE=silakka54.vil
LAYOUT_FILE_TMP="${LAYOUT_FILE}.tmp"
jq . $LAYOUT_FILE > $LAYOUT_FILE_TMP && mv $LAYOUT_FILE_TMP $LAYOUT_FILE
python3 generate_layout.py $LAYOUT_FILE
git add $LAYOUT_FILE ${LAYOUT_FILE%.vil}.html
git commit -m "${1:-Update layout}"
