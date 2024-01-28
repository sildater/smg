import mido
import time
"""
test the message produced by the foot switch on the mpkmini.
"""

print(mido.get_output_names(), mido.get_input_names())

"""
iport  = mido.open_input('MPKmini2 4')
oport = mido.open_output('seq 2')

"""

def g(iport, oport, ref_note):
    channel_0_pitch = ref_note % 12
    channel_3 = (channel_0_pitch + 4) % 12
    channel_5 = (channel_0_pitch + 7) % 12
    # channel 0 is used for ref note and then up the scale, so MPE can be used for pitching
    try:
        while True:
            time.sleep(0.001)
            for msg in iport.iter_pending():
                # print(msg)
                if msg.type in ["note_on", "note_off"]:
                    pitch =msg.note 
                    channel = (pitch % 12 - channel_0_pitch) % 12
                    nmsg = msg.copy(channel = channel)
                    oport.send(nmsg)
                    print("NOTE: ", msg, nmsg)

                if msg.type == "control_change":
                    if msg.control == 1:
                        npitch = int(msg.value/127 * 8192 / 2) # only shift by 1 semitone
                        nmsg = mido.Message(type="pitchwheel", 
                                            channel = channel_3, 
                                            pitch = npitch)
                        oport.send(nmsg)
                        print("WHEEL ",msg, nmsg)
                    
                if msg.type == "pitchwheel":
                    npitch = msg.pitch# int(msg.pitch / 8192 * 256) # shift by 2 semitones
                    nmsg = msg.copy(channel = channel_5,
                                    pitch = npitch)
                    oport.send(nmsg)
                    print("WHEEL ",msg, nmsg)
    except KeyboardInterrupt:
        print("stop")

           
        
def h(iport, oport):
    iport.close()
    oport.close()

