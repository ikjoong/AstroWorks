#===========================================================================================
proc cmd_texteditor {{tfile "" } } {
	#---
	variable w
	variable target_file
	variable todolist
	#---
	set target_file $tfile
	set todolist ""
	#---
	if {$target_file == ""} {
		set target_file "to_do_list.txt"
	}
	#---
	if {![file exists $target_file]} {
		set f [open $target_file w]
		close $f
	} else {
		set f [open $target_file r]
		set todolist [read $f]
		close $f
	}
	#---
	set w ".texteditor"
	if [winfo exists $w] {
		destroy $w
	}
	## Create GUI
	set w [toplevel $w ]
	wm attribute $w -topmost 0
	wm geometry $w 500x400+1100+50
	#wm geometry $w 200x100+1100+50
	#wm geometry $w +3400+-1500 ; #-- upper window
	#wm geometry $w +3400+100 ; #-- right window
	#wm geometry $w +1200+100 ; #-- left window
	#wm title $w "[split [split $target_file "."] 0]"
	wm title $w "To do list"
	#-----------------------
	frame $w.mb
	button $w.mb.btn1 -text "Save" -command {SaveFile}
	#button $w.mb.btn2 -text "Clear" -command {ClearEdit}
	button $w.mb.btn3 -text "Exit" -command {QuitFile}
	#
	pack $w.mb.btn1   -side left  -padx 2m -fill x -expand yes
	#pack $w.mb.btn2   -side left  -padx 2m -fill x -expand yes
	pack $w.mb.btn3   -side left  -padx 2m -fill x -expand yes
	#
	frame $w.te -relief raised -borderwidth 2 
	#
	#Shows how to control text widget scrolling using a scrollbar
	#First set up scrollbar
	scrollbar $w.te.vscroll -relief sunken -command "$w.te.edit1 yview"
	#Set up a text widget and link scroll
	set family Courier
	text $w.te.edit1 -yscroll "$w.te.vscroll set" -font "$family 12"
	#Pack editing components
	pack $w.te.vscroll -anchor nw  -side right -fill y
	pack $w.te.edit1 -anchor nw -expand yes -fill both
	#Now pack everything together
	pack $w.mb  -anchor nw -pady 2m 
	pack $w.te  -anchor nw -pady 2m -fill both -expand 1
	#--------------------------------------------------------
		$w.te.edit1 insert 1.0 $todolist
	#--------------------------------------------------------
	proc NewFile {} {
		variable w
		#puts "NewFile not implemented yet"
		variable filename
		#Could have anguish here - should we prompt
		#the user for confirmation?
		#Should we check to see if text exists in window?
		#Should we check to see if file has changed?
		#Should we check to see if file has been saved?
		##
		#Brutal implementation!
		$w.te.edit1 delete 1.0 end
		set filename "New"
		wm title . "EDIT: $filename" 
	}
	#--------------------------------------------------------
	proc LoadFile {} {
		variable w
		#puts "LoadFile not implemented yet"
		variable filename
		#First get text from file
		set fn [ GetFileName ]
		set f [open $fn r]
		set x [read $f]
		#Clear the window!
		ClearEdit
		#Insert the new text
		$w.te.edit1 insert 1.0 $x
		set t [close $f]
		#Set global filename
		set filename $fn
		wm title . "EDIT : $filename"
	}
	#--------------------------------------------------------
	proc SaveFile {} {
		#-------------------
		variable w
		variable target_file
		variable todolist
		#-------------------
		set f [open $target_file w]
		set lns [$w.te.edit1 get 1.0 end]
		puts $f $lns
		close $f
		return
		#-------------------
	}
	#--------------------------------------------------------
	proc SaveAsFile {} {
		variable w
		#puts "SaveAsFile not implemented yet"
		variable filename
		#Get file name to save
		set fn [ GetFileName ]
		set f [open $fn w]
		#Get text to save
		set x [$w.te.edit1 get 1.0 end]
		#Save it
		puts $f $x
		#and close file
		set t [close $f]
		#Set global filename
		set filename $fn
		wm title . "EDIT : $filename"
	}
	#--------------------------------------------------------
	proc QuitFile {} {
		variable w
		#puts "QuitFile not implemented yet"
		#Could have anguish here - should we prompt
		#the user for confirmation?
		#Should we check to see if file has changed?
		#Should we check to see if file has been saved?
		#
		#This implementation is brutal!
		#destroy .
		destroy $w
	}
	#--------------------------------------------------------
	proc ClearEdit { } {
		variable w
		#puts "ClearEdit not implemented yet"
		#Could have anguish here - should we prompt
		#the user for confirmation?
		#Should we check to see if file has changed?
		#Should we check to see if file has been saved?
		#
		$w.te.edit1 delete 1.0 end	
	}
	#--------------------------------------------------------
	proc GetFileName { } {
		set types {
			    {{Text Files}       {.txt}        }
			    {{TCL Scripts}      {.tcl}        }
			    {{C Source Files}   {.c}      TEXT}
			    {{GIF Files}        {.gif}        }
			    {{GIF Files}        {}        GIFF}
			    {{All Files}        *             }
		}
		set fn [tk_getOpenFile -filetypes $types]
		return $fn
	}
	#--------------------------------------------------------
}
#--------------------------------
cmd_texteditor
