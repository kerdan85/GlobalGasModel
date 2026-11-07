# ======================================================================
#  nature_esl_figures.R
#
#  Nature-grade publication figures for the Energy Sovereignty Leakage
#  (ESL) results. Reads outputs/esl_results.csv (produced by run_esl.py)
#  and writes vector + raster figures to outputs/figures/R/.
#
#  Figures produced:
#    Fig 2a  ESL_leakage_contrast   - plateau vs spare-capacity ESL(%)
#    Fig 2b  ESL_coal_mechanism     - coal displaced abroad (BCM)
#    Fig 3   ESL_emissions_dualGWP  - net Mt CO2e, GWP100 vs GWP20
#    Fig 2   ESL_main_2panel        - (a)+(b) combined main figure
#
#  Run from the model root:
#     Rscript R/nature_esl_figures.R
#  or in RStudio set the working directory to the model root first:
#     setwd("/path/to/GlobalGasModel"); source("R/nature_esl_figures.R")
#
#  Packages: ggplot2, dplyr, tidyr, scales, patchwork
#     install.packages(c("ggplot2","dplyr","tidyr","scales","patchwork"))
#  (No forcats / no tidyverse meta-package required.)
# ======================================================================

suppressPackageStartupMessages({
  library(ggplot2); library(dplyr); library(tidyr)
  library(scales);  library(patchwork)
})

# ---- paths (robust to where Rscript is launched from) ----------------
root    <- if (file.exists("outputs/esl_results.csv")) "." else
           if (file.exists("GlobalGasModel/outputs/esl_results.csv")) "GlobalGasModel" else "."
in_csv  <- file.path(root, "outputs", "esl_results.csv")
out_dir <- file.path(root, "outputs", "figures", "R")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
stopifnot(file.exists(in_csv))

# 1 model emission-unit (gCO2e/MJ x BCM) -> Mt CO2e  (1 BCM gas ~ 36 PJ)
MU_TO_MT <- 0.036

# ---- load & tidy -----------------------------------------------------
d <- read.csv(in_csv, stringsAsFactors = FALSE)
# normalise the Plateau column to a logical regardless of True/False/0/1
d$Plateau <- tolower(as.character(d$Plateau)) %in% c("true", "1", "t")
d <- d %>%
  mutate(Regime = ifelse(Plateau, "US at plateau (supply-constrained)",
                                   "US with spare capacity"),
         e100_Mt = d_emis_GWP100 * MU_TO_MT,
         e20_Mt  = d_emis_GWP20  * MU_TO_MT)

# ======================================================================
#  Nature-style theme
# ======================================================================
pal <- c("US at plateau (supply-constrained)" = "#b2182b",
         "US with spare capacity"             = "#2166ac")
pal_emis <- c("GWP100 (100-yr)" = "#e0a030", "GWP20 (20-yr)" = "#d1495b")
col_coal <- "#6e6e6e"

theme_nature <- function(base = 12) {
  theme_classic(base_size = base, base_family = "") +
    theme(
      plot.title      = element_text(face = "bold", size = base + 1, hjust = 0),
      plot.subtitle   = element_text(size = base - 1, colour = "grey30"),
      axis.title      = element_text(size = base),
      axis.text       = element_text(colour = "black", size = base - 1),
      axis.ticks      = element_line(colour = "black", linewidth = 0.4),
      axis.line       = element_line(colour = "black", linewidth = 0.4),
      legend.position = c(0.02, 0.98),
      legend.justification = c(0, 1),
      legend.title    = element_blank(),
      legend.background = element_rect(fill = scales::alpha("white", 0.6), colour = NA),
      legend.key.height = unit(11, "pt"),
      plot.margin     = margin(10, 14, 8, 10)
    )
}

yrs <- sort(unique(d$Year))

# ======================================================================
#  Fig 2a | Leakage contrast (plateau vs spare capacity)
# ======================================================================
p_contrast <- ggplot(d, aes(Year, ESL_pct, colour = Regime, shape = Regime)) +
  geom_hline(yintercept = 100, linetype = 3, colour = "grey55") +
  geom_line(aes(linetype = Regime), linewidth = 1.1) +
  geom_point(size = 3.2, stroke = 0.8, fill = "white") +
  scale_colour_manual(values = pal) +
  scale_shape_manual(values = c(21, 22)) +
  scale_linetype_manual(values = c("solid", "longdash")) +
  scale_x_continuous(breaks = yrs) +
  scale_y_continuous(limits = c(-5, 125), breaks = seq(0, 120, 20),
                     expand = expansion(mult = c(0, 0.02))) +
  labs(title = "a",
       subtitle = "Leakage is conditional on US supply tightness",
       x = NULL, y = "Energy Sovereignty Leakage (%)") +
  theme_nature() +
  guides(colour = guide_legend(override.aes = list(size = 2.6)))

# ======================================================================
#  Fig 2b | Coal-to-gas displacement mechanism (plateau case)
# ======================================================================
dp <- filter(d, Plateau)
p_coal <- ggplot(dp, aes(Year)) +
  geom_col(aes(y = Displaced, fill = "Gas freed by Mexico (BCM)"),
           width = 2.6, alpha = 0.45) +
  geom_line(aes(y = d_coal_displaced, colour = "Coal displaced abroad (BCM)"),
            linewidth = 1.1) +
  geom_point(aes(y = d_coal_displaced, colour = "Coal displaced abroad (BCM)"),
             size = 3) +
  scale_fill_manual(values = c("Gas freed by Mexico (BCM)" = "#c6dbef")) +
  scale_colour_manual(values = c("Coal displaced abroad (BCM)" = col_coal)) +
  scale_x_continuous(breaks = yrs) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  labs(title = "b",
       subtitle = "Freed gas is absorbed by displacing coal in Asia",
       x = NULL, y = expression("BCM "*yr^{-1})) +
  theme_nature() +
  theme(legend.position = c(0.02, 0.98))

# ======================================================================
#  Fig 3 | Dual-GWP emissions ledger (plateau case), in Mt CO2e
# ======================================================================
emis <- dp %>%
  select(Year, e100_Mt, e20_Mt) %>%
  pivot_longer(-Year, names_to = "horizon", values_to = "Mt") %>%
  mutate(horizon = recode(horizon,
                          e100_Mt = "GWP100 (100-yr)",
                          e20_Mt  = "GWP20 (20-yr)"))

p_emis <- ggplot(emis, aes(factor(Year), Mt, fill = horizon)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.62) +
  geom_hline(yintercept = 0, colour = "black", linewidth = 0.4) +
  scale_fill_manual(values = pal_emis) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.08))) +
  labs(title = "Leakage raises global emissions",
       subtitle = expression("Net change attributable to leakage; shale-LNG > coal, especially at GWP"[20]),
       x = NULL, y = expression("Net "*Delta*" emissions (Mt CO"[2]*"e "*yr^{-1}*")")) +
  theme_nature() +
  theme(legend.position = c(0.02, 0.98))

# add value labels on the GWP20 bars (the headline)
p_emis <- p_emis +
  geom_text(data = filter(emis, horizon == "GWP20 (20-yr)", Mt > 1),
            aes(label = round(Mt)), vjust = -0.5, size = 3,
            colour = pal_emis[["GWP20 (20-yr)"]],
            position = position_dodge(width = 0.7))

# ======================================================================
#  Combined main figure (2a + 2b)
# ======================================================================
main2 <- p_contrast + p_coal + plot_layout(widths = c(1, 1))

# ======================================================================
#  Save (PDF vector for submission + 300-dpi PNG for preview)
# ======================================================================
save_fig <- function(plot, name, w, h) {
  ggsave(file.path(out_dir, paste0(name, ".pdf")), plot, width = w, height = h, device = cairo_pdf)
  ggsave(file.path(out_dir, paste0(name, ".png")), plot, width = w, height = h, dpi = 300)
}

save_fig(p_contrast, "ESL_leakage_contrast", 6.0, 4.5)
save_fig(p_coal,     "ESL_coal_mechanism",   6.0, 4.5)
save_fig(p_emis,     "ESL_emissions_dualGWP",6.8, 4.6)
save_fig(main2,      "ESL_main_2panel",      11.0, 4.6)

cat("Figures written to", out_dir, "\n")
cat("  ESL_leakage_contrast.[pdf|png]\n  ESL_coal_mechanism.[pdf|png]\n",
    " ESL_emissions_dualGWP.[pdf|png]\n  ESL_main_2panel.[pdf|png]\n", sep = "")
