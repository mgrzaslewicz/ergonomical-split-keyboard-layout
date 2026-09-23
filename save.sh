LAYOUT_FILE=silakka54.vil
LAYOUT_FILE_TMP="${LAYOUT_FILE}.tmp"
jq . $LAYOUT_FILE > $LAYOUT_FILE_TMP && mv $LAYOUT_FILE_TMP $LAYOUT_FILE
git add $LAYOUT_FILE
git commit -m "Update layout" -m "$@"
