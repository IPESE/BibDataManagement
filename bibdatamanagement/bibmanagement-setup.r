knitr::opts_chunk$set(echo = F, message = F, warning = F)
options(scipen=999)

if (!require(reticulate)) {
install.packages("reticulate")
}
if (!require(dplyr)) {
install.packages("dplyr")
}
if (!require(knitr)) {
install.packages("knitr")
}
if (!require(kableExtra)) {
install.packages("kableExtra")
}
if (!require(htmlwidgets)) {
install.packages("htmlwidgets", repos = "http://cran.us.r-project.org")
}
library("htmlwidgets")
library("plotly")
library("reticulate")
library("kableExtra")
library("jsonlite")
library("dplyr")

# venv <- NULL
# if (length(rmarkdown::metadata$venv) > 0) {venv <- rmarkdown::metadata$venv} else {venv <- "./venv"}
# if (!(dir.exists(venv))) {
#   virtualenv_create(venv)
# }

# use_virtualenv(venv, required = T)

# packages <- list('pybtex', 'plotly', 'pandas', 'bibdata_management')
# for (pack in packages){
#   if (!(py_module_available(pack))){
#     if (pack == 'bibdata_management'){
#       virtualenv_install(venv, "bibdatamanagement", pip_options = "--index-url=https://ipese-internal.epfl.ch/registry/pypi/ --upgrade")
#     }
#     else{
#       virtualenv_install(venv, pack)
#     }
#   }
# }

use_python('C:/Users/User/AppData/Local/Programs/Python/Python310/')
py_run_string("from bibdata_management import *")

set_rbibdata_ui <- function(){
  py_run_string("from bibdata_management import *")
  if (length(rmarkdown::metadata) > 0) {
    bib_path <- rmarkdown::metadata$bibliography
    if (length(rmarkdown::metadata$params$default_values) > 0) {
      default_values <- rmarkdown::metadata$params$default_values
    } else {
      py_run_string("get_file('parameters_description.csv', 'files/parameters_description.csv')")
      default_values <- 'files/parameters_description.csv'
    }

    py_run_string(paste0("rbibdata_ui = RBibData('", bib_path, "' , '" , default_values, "')"))
    rbibdata_ui <- py$rbibdata_ui
    return(rbibdata_ui)
  } else {
    return("No bibliography")
  }
}

#' Execute rbibdata code with options
#'
#' This function executes the rbibdata code with the specified options.
#'
#' @param options Options from the chunk.
#'   Contains a "code" element specifying that rbibdata executes.
#' @return The result of executing the rbibdata code.
#'
#' @export
eng_rbibdata <- function(options) {
  if (options$eval) {
    out <- do.call(rbibdata, list(options$code))
    out
  }
}

#' Process rbibdata result based on different cases
#'
#' This function processes the result of executing the rbibdata code based on different cases.
#' It handles cases where the result is a custom view table, a plot, or data to be stored in the `data` variable.
#' For other cases, it returns the original code.
#'
#' @param code The rbibdata code to process.
#' @return Depending on the case, it returns either a table, a plot, data, or the original code.
#' @export
rbibdata <- function(code) {
  result <- rbibdata_ui$read_chunk(code)
  if(result[[1]] == T) {
    if(result[[2]] == 'custom_view'){
      table <- kable(result[[3]], align = 'llrlrr', escape = FALSE, caption = "Model parameters") %>%
        kable_styling(bootstrap_options = c('striped', 'hover')) %>%
        add_footnote(label=result[[4]], notation = 'number', escape = F)
      return(table)
    } else if(result[[2]] == 'plot'){
      plot <- eval(parse(text = result[[3]]))
      p <- plotly::plotly_build(plot)
      return(p)
    } else {
      code
    }
  }
}


options(scipen=999)
knitr::opts_chunk$set(out.width="100%")
def.chunk.hook  <- knitr::knit_hooks$get("chunk")
knitr::knit_hooks$set(chunk = function(x, options) {
  x <- def.chunk.hook(x, options)
  ifelse(options$size != "normalsize", paste0("\n \\", options$size,"\n\n", x, "\n\n \\normalsize"), x)
})

rbibdata_ui <- set_rbibdata_ui()
knitr::knit_engines$set(rbibdata = eng_rbibdata)
