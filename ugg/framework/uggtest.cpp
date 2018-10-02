// uggtest.cpp -- try running ugg framework test
// 
// Roger B. Dannenberg
// Jun 2017

#include <iostream>
#include "assert.h"
#include "portaudio.h"
#include "ugen.h"
#include "osci.h"
#include "decay.h"
#include "add.h"
#include "mult.h"


/*
#ifdef __APPLE__
#include "pa_mac_core.h"
#endif
*/

#define NUM_SECONDS 6
#define NUM_SAW_HARMONICS 20

using namespace std; 

#define TABLE_SIZE 512

Table_ptr SINETABLE;

Ugen *left_ugen = NULL;
Ugen *right_ugen = NULL;



static int ugg_callback(const void *inputBuffer, void *outputBuffer,
                       unsigned long framesPerBuffer,
                       const PaStreamCallbackTimeInfo* timeInfo,
                       PaStreamCallbackFlags statusFlags,
                       void *userData)
{
    float *out = (float *) outputBuffer;
    unsigned long i;

    (void) timeInfo; /* Prevent unused variable warnings. */
    (void) statusFlags;
    (void) inputBuffer;
    
    left_ugen->run(ugg_block_count);
    right_ugen->run(ugg_block_count);
    ugg_block_count++;
    sample *left = left_ugen->get_outs();
    sample *right = right_ugen->get_outs();
    assert(framesPerBuffer == BL);
    for (i = 0; i < framesPerBuffer; i++) {
        *out++ = left[i]; // left
        *out++ = right[i]; // right
    }
    
    return paContinue;
}

// make running sum of tones of freq
//
void add_tone(Ugen_ptr &sum, float freq, sample gain, Table_ptr sawtooth)
{
    Osci_ccc_a *osc = new Osci_ccc_a(freq, 0.0, sawtooth);
    Decay_cc_a *decay = new Decay_cc_a(1.0F * gain, NUM_SECONDS - 1);
    Mult_aa_a *mult = new Mult_aa_a(osc, decay);
    if (sum) {
        *sum = Add_aa_a(sum, mult);
    } else {
        sum = mult;
    }
}


/*******************************************************************/

int main(void)
{
    PaStreamParameters outputParameters;
    PaStream *stream;
    PaError err;
/*
#ifdef __APPLE__
    PaMacCoreStreamInfo macInfo;
#endif
*/
    int i, h;

    srand(time(0)); // randomize seed

    SINETABLE = table_create(TABLE_SIZE);
    /* initialise sinusoidal wavetable */
    for (i = 0; i <= TABLE_SIZE; i++) {
        tblput(SINETABLE, i, (sample) sin(((double) i / (double) TABLE_SIZE) * M_PI * 2.0));
    }

    Table_ptr sawtooth = table_create(TABLE_SIZE);
    for (i = 0; i <= TABLE_SIZE; i++) {
        sample y = 0;
        for (h = 1; h <= NUM_SAW_HARMONICS; h++) {
            y += (sample) sin(((double) (i * h) / (double) TABLE_SIZE) * M_PI * 2.0) / (sample) h;
        }
        tblput(sawtooth, i, y);
    }
    for (i = 0; i <= TABLE_SIZE; i++) {
        printf("sawtooth[%d] = %f\n", i, tblget(sawtooth, i));
    }

    const int nfreqs = 4;
    float freqs[nfreqs] = {166, 220, 247.5, 185.625};

    Ugen *left_sum = NULL;
    Ugen *right_sum = NULL;

    for (i = 0; i < nfreqs; i++) {
        add_tone(left_sum, freqs[i] / 2, 0.125, sawtooth);
        add_tone(right_sum, freqs[i] / 2 + 2, 0.125, sawtooth);
    }
    left_ugen = left_sum;
    right_ugen = right_sum;

    err = Pa_Initialize();
    if (err != paNoError) goto error;

    /* default output device */
    outputParameters.device = Pa_GetDefaultOutputDevice();
    if (outputParameters.device == paNoDevice) {
        fprintf(stderr,"Error: No default output device.\n");
        goto error;
    }
    outputParameters.channelCount = 2;       /* stereo output */
    outputParameters.sampleFormat = paFloat32; /* 32 bit float output */
    outputParameters.suggestedLatency = 
            Pa_GetDeviceInfo(outputParameters.device)->defaultLowOutputLatency;
    outputParameters.hostApiSpecificStreamInfo = NULL;
    /** setup host specific info */
/*
#ifdef __APPLE__
    PaMacCore_SetupStreamInfo(&macInfo, paMacCorePro);
    outputParameters.hostApiSpecificStreamInfo = &macInfo;
#endif
*/
    err = Pa_OpenStream(&stream,
                        NULL, /* no input */
                        &outputParameters,
                        AR,
                        BL,
                        paClipOff, /* no clipping */
                        ugg_callback,
                        NULL);
    if (err != paNoError) goto error;

    err = Pa_StartStream(stream);
    if (err != paNoError) goto error;

    printf("Play for %d seconds.\n", NUM_SECONDS);
    Pa_Sleep(NUM_SECONDS * 1000);

    err = Pa_StopStream(stream);
    if (err != paNoError) goto error;

    err = Pa_CloseStream(stream);
    if (err != paNoError) goto error;

    Pa_Terminate();
    printf("uggtest finished.\n");
    
    return err;
error:
    Pa_Terminate();
    fprintf(stderr, "An error occured while using the portaudio stream\n");
    fprintf(stderr, "Error number: %d\n", err);
    fprintf(stderr, "Error message: %s\n", Pa_GetErrorText(err));
    return err;
}
