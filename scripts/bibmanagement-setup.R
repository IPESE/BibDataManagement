knitr::opts_chunk$set(echo = F, message = F, warning = F)
options(scipen=999)
options(repos = c(CRAN = "https://cran.r-project.org"))

if (!require(reticulate)) {
install.packages("reticulate")
}
if (!require(dplyr)) {
install.packages("dplyr")
}
if (!require(rmarkdown)) {
install.packages("rmarkdown")
}
if (!require(kableExtra)) {
install.packages("kableExtra")
}
if (!require(htmlwidgets)) {
install.packages("htmlwidgets")
}
library("htmlwidgets")
library("plotly")
library("reticulate")
library("kableExtra")
library("jsonlite")
library("dplyr")

venv <- NULL
if (length(rmarkdown::metadata$venv) > 0) {venv <- rmarkdown::metadata$venv} else {venv <- "./venv"}
if (!(dir.exists(venv))) {
  virtualenv_create(venv)
}

use_virtualenv(venv, required = T)

packages <- list('pybtex', 'plotly', 'pandas', 'bibdata_management')
for (pack in packages){
  if (!(py_module_available(pack))){
    if (pack == 'bibdata_management'){
      virtualenv_install(venv, 'bibdatamanagement')
    }
    else{
      virtualenv_install(venv, pack)
    }
  }
}

# use_python('C:/Users/User/AppData/Local/Programs/Python/Python310/')
py_run_string("from bibdata_management import *")

set_rbibdata_ui <- function(){
  py_run_string("from bibdata_management import *")
  if (length(rmarkdown::metadata) > 0) {
    bib_path <- rmarkdown::metadata$bibliography
    if (length(rmarkdown::metadata$params$default_values) > 0) {
      default_values <- rmarkdown::metadata$params$default_values
      py_run_string(paste0("rbibdata_ui = RBibData('", bib_path, "' , '" , default_values, "')"))
      
    } else {
      py_run_string("get_file('parameters_description.csv', 'files/parameters_description.csv')")
      default_values <- 'files/parameters_description.csv'
      py_run_string(paste0("rbibdata_ui = RBibData('", bib_path, "')"))
      message('You did not give any default parameters description. An example was provided to you in files/parameters_description.csv')
      
    }

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
  print(knitr::opts_current$get("label"))
  if (options$eval) {
    out <- do.call(rbibdata, list(options$code))
    out
    # result <- knitr::engine_output(options, options$code, out)
  }
  # return(eval(paste(result, sep = "\n\n")))
}

#' Process code in the chunk and rbibdata result based on different cases
#'
#' This function processes the code and the result of executing the rbibdata code based on different cases.
#' First it looks at if there is any definition of variable from R environment and get the value.
#' Then, it handles cases where the result is a custom view table, a plot, or data to be stored in the `data` variable.
#' For other cases, it returns the original code.
#'
#' @param code The rbibdata code to process.
#' @return Depending on the case, it returns either a table, a plot, data, or the original code.
#' @export
rbibdata <- function(code) {
  input_code <- code
  r_variables <- grepl("`r\\..+`", code) 
  for (i in 1:length(r_variables)) {
    if (r_variables[i] == TRUE) {
        isolated_var <- gsub(".*(`r\\..+`).*", "\\1", code[i])
        isolated_var <- substr(isolated_var, 4, nchar(isolated_var) - 1)
        isolated_var <- eval(parse(text = isolated_var)) 
        code[i] <- gsub("`r\\..+`", isolated_var , code[i])
    }
  }
  result <- rbibdata_ui$read_chunk(code)
  if(result[[1]] == T) {
    if(result[[2]] == 'custom_view'){
      if(knitr::is_html_output()){
        table <- kable(result[[3]], align = 'llrllr', escape = FALSE, caption = "Model parameters") %>%
          kable_styling(bootstrap_options = c('striped', 'hover', 'condensed', 'responsive'), font_size = 12) %>%
          add_footnote(label=result[[4]], notation = 'number', escape = F) 
      }
      else{
        table <- kable(result[[3]], align = 'llrllr', escape = FALSE, caption = "Model parameters", format="markdown") %>%
          kable_styling(bootstrap_options = c('striped', 'hover', 'condensed', 'responsive'), font_size = 12) %>%
          add_footnote(label=result[[4]], notation = 'number', escape = F) 
      }
      if ('Comment' %in% colnames(result[[3]])){
        index <- which(colnames(result[[3]]) == "Comment")[1]
        table <- table %>%
          column_spec(index, width_min = "15em")
      }
      return(table)
    } else if(result[[2]] == 'plot'){
      plot <- eval(parse(text = result[[3]]))
      p <- plotly::plotly_build(plot)
      return(p)
    } else {
      if (length(input_code) > 1) {
        code <- "```{r}\n"
        for (line in input_code) {
          code <- paste(code, line, '\n')
        }
        code <- paste(code, "\n```")
      } else {
        code <- paste("```{r}\n", input_code, "\n```")
      }
      eval(code)
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
