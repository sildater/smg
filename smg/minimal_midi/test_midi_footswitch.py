import mido
"""
test the message produced by the foot switch on the mpkmini.
"""

print(mido.get_output_names(), mido.get_input_names())

iport  = mido.open_input('MPKmini2 1')
    
def g():
    for msg in iport:
        # if msg.is_cc():
        #     # 2 = breath, 3 too?, 11, 9
        #     # 4 button
        #     if msg.control == 95:# in [2,3,9,11]: 
        print(msg)
        
def h():
    global iport
    iport.close()


# control_change channel=0 control=64 value=0 time=0
# control_change channel=0 control=64 value=127 time=0