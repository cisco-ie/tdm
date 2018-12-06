# TDM Documentation

TDM is documented via [VuePress](https://vuepress.vuejs.org/), written in Markdown and converted via VuePress to HTML to be deployed alongside TDM. This allows us to write our documentation in Markdown, and not be responsible for hand-coding HTML documentation documents. This does break some level of GitHub-like navigation, but results in a nice, self-hosted documentation site.

```bash
# Run dev server on localhost:8089
./standalone.sh
```

## Manual Navigation
If you do not want to run the standalone server or production TDM, you may navigate through this repositories Markdown documents but the links might be more difficult to navigate.

* Documentation  
`docs/*` except `.vuepress`
* Static Content  
`docs/.vuepress/public`
