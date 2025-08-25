
; L&I Insurance AutoHotkey Scraper
#NoEnv
SendMode Input

; Function to scrape one USDOT
ScrapeUSDOT(usdot) {
    ; Open browser to L&I
    Run, chrome.exe "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
    Sleep, 3000
    
    ; Enter USDOT
    Send, {Tab 5}  ; Navigate to input field
    Send, %usdot%
    
    ; Submit form
    Send, {Enter}
    Sleep, 3000
    
    ; Click Active Insurance (use image search or coordinates)
    ; You'll need to find the exact position
    Click, 500, 400  ; Adjust coordinates
    
    Sleep, 3000
    
    ; Select all and copy
    Send, ^a
    Send, ^c
    
    ; Parse clipboard and save
    ; ... parsing logic ...
}

; Main loop
Loop {
    ; Read pending USDOTs from file
    FileRead, pending, li_pending.txt
    
    Loop, Parse, pending, `n
    {
        if (A_LoopField != "") {
            ScrapeUSDOT(A_LoopField)
            Sleep, 5000
        }
    }
    
    ; Wait 1 hour before next run
    Sleep, 3600000
}
        