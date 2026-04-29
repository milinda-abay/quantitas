#!/usr/bin/env bash
input=$(cat)

model=$(echo "$input"  | jq -r '.model.display_name // "unknown"')
effort=$(echo "$input" | jq -r '.effort.level // ""')
pct=$(echo "$input"    | jq -r 'if .context_window.used_percentage != null then (.context_window.used_percentage | floor | tostring) else "-1" end')
tin=$(echo "$input"    | jq -r '.context_window.total_input_tokens // -1')
tout=$(echo "$input"   | jq -r '.context_window.total_output_tokens // -1')
five_hr=$(echo "$input" | jq -r 'if .rate_limits.five_hour.used_percentage != null then (.rate_limits.five_hour.used_percentage | floor | tostring) else "" end')
resets_at=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // ""')
cwd=$(echo "$input"    | jq -r '.workspace.current_dir // ""')

# Format resets_at (Unix timestamp) as local HH:MM
resets_str=""
if [[ -n "$resets_at" && "$resets_at" != "null" ]]; then
    resets_str=$(TZ="Australia/Melbourne" date -d "@${resets_at}" "+%H:%M" 2>/dev/null)
fi

# Effort colors matched to /effort command display
effort_colored=""
if [[ -n "$effort" ]]; then
    case "$effort" in
        low)    ec="\e[38;2;212;160;23m"  ;;
        medium) ec="\e[38;2;78;201;78m"   ;;
        high)   ec="\e[38;2;86;156;214m"  ;;
        xhigh)  ec="\e[38;2;192;132;252m" ;;
        max)    ec="\e[38;2;191;77;67m"   ;;
        *)      ec="" ;;
    esac
    effort_colored="${ec}effort:${effort}\e[0m"
fi

# Line 1: model | effort | tok in | tok out | cwd
line1="\e[38;2;97;170;242m${model}\e[0m"
[[ -n "$effort_colored" ]] && line1+=" | $effort_colored"
[[ "$tin"  -ge 0 ]] 2>/dev/null && line1+=" | \e[38;2;235;219;188mtok in:${tin}\e[0m"
[[ "$tout" -ge 0 ]] 2>/dev/null && line1+=" | \e[38;2;212;162;127mtok out:${tout}\e[0m"
[[ -n "$cwd" ]] && line1+=" | \e[38;2;204;120;92m${cwd}\e[0m"

# Line 2: context bar | cost | duration
line2=""
if [[ "$pct" -ge 0 ]] 2>/dev/null; then
    filled=$((pct / 10))
    empty=$((10 - filled))
    if   [[ "$pct" -le 33 ]]; then color="\e[38;2;235;219;188m"
    elif [[ "$pct" -le 60 ]]; then color="\e[38;2;212;162;127m"
    else                            color="\e[38;2;204;120;92m"
    fi
    dim="\e[38;2;80;80;80m"
    reset="\e[0m"
    bar=""
    for ((i=0; i<filled; i++)); do bar+="${color}█"; done
    for ((i=0; i<empty;  i++)); do bar+="${dim}░"; done
    bar+="${reset}"
    line2="${color}ctx:${reset}[${bar}] ${color}${pct}%${reset}"
fi

# Usage bar: rate_limits.five_hour.used_percentage in light blue
if [[ -n "$five_hr" && "$five_hr" -ge 0 ]] 2>/dev/null; then
    u_filled=$((five_hr / 10))
    u_empty=$((10 - u_filled))
    u_color="\e[38;2;100;200;255m"
    u_dim="\e[38;2;80;80;80m"
    u_reset="\e[0m"
    u_bar=""
    for ((i=0; i<u_filled; i++)); do u_bar+="${u_color}█"; done
    for ((i=0; i<u_empty;  i++)); do u_bar+="${u_dim}░"; done
    u_bar+="${u_reset}"
    [[ -n "$line2" ]] && line2+=" | "
    line2+="${u_color}usage:${u_reset}[${u_bar}] ${u_color}${five_hr}%${u_reset}"
fi

[[ -n "$resets_str" ]] && { [[ -n "$line2" ]] && line2+=" | "; line2+="\e[38;2;86;182;194mresets:${resets_str}\e[0m"; }

printf "%b\n" "$line1"
[[ -n "$line2" ]] && printf "%b\n" "$line2"
