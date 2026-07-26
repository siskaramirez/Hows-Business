suppressPackageStartupMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1 || (args[1] != "-" && !file.exists(args[1]))) {
    cat(toJSON(list(status = "failed", error = "A valid JSON input is required."), auto_unbox = TRUE))
    quit(status = 1)
}

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- if (length(script_arg) > 0) {
    normalizePath(sub("^--file=", "", script_arg[1]), winslash = "/")
} else {
    normalizePath("run_insights.R", winslash = "/")
}
source(file.path(dirname(script_path), "insights.R"))

result <- tryCatch(
    {
        input_json <- if (args[1] == "-") {
            paste(readLines(file("stdin"), warn = FALSE), collapse = "\n")
        } else {
            paste(readLines(args[1], warn = FALSE, encoding = "UTF-8"), collapse = "\n")
        }
        payload <- fromJSON(input_json, simplifyDataFrame = TRUE)
        generate_business_insights(payload$records)
    },
    error = function(error) {
        list(status = "failed", error = conditionMessage(error))
    }
)

cat(toJSON(result, auto_unbox = TRUE, null = "null", dataframe = "rows"))
