from toptica.lasersdk.client import Client, NetworkConnection, DeviceNotFoundError, \
                                    DecopError, DecopValueError, UserLevel
from toptica.lasersdk.utils.dlcpro import *
import logging
import numpy as np
import time
import functools
import sys

def InterfaceErrorWrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (DeviceNotFoundError, DecopError, DecopValueError) as err:
            try:
                func_name = sys._getframe(1).f_code.co_name
            except:
                func_name = func.__name__
            logging.warning("DLCProCs warning in {0}() : ".format(func_name) \
                            + str(err))

            return np.nan
    return wrapper


class checkTypeWrapper(object):
    def __init__(self, **kwargsValidate):
        self.kwargs_validate = kwargsValidate

    def __call__(self, func, *args, **kwargs):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(kwargs) == 0:
                logging.warning('DLCProCs warning in {0} : function requires keyword arguments'.format(func.__name__))
                return np.nan
            invalid_type = False
            for k, v in self.kwargs_validate.items():
                if not isinstance(kwargs[k], v):
                    if isinstance(v, type):
                        logging.warning('DLCProCs warning in {0} : {1} not {2}'.format(func.__name__, k, v.__name__))
                    elif isinstance(v, (list, tuple)):
                        logging.warning('DLCProCs warning in {0} : {1} not {2}'.format(func.__name__, k, [val.__name__ for val in v]))
                    else:
                        logging.warning('DLCProCs warning in {0} : {1} not {2}'.format(func.__name__, k, v))
                    invalid_type = True
            if invalid_type:
                return np.nan
            else:
                return func(*args, **kwargs)
        return wrapper

class DLCPro:
    def __init__(self, time_offset, COM_port):
        self.COM_port = COM_port
        self.time_offset = time_offset

        self.new_attributes = []
        self.dtype = 'f16'
        self.shape = (6,)

        self.warnings = []

        self.verification_string = self.laserProductName(laser = 1)
        if not isinstance(self.verification_string, str):
            self.verification_string = False

        # see DLCPro Manual p.220 (Appendix 4.1)
        self.signalsNumDesc = {
                        -3 : 'None',
                        -2 : 'time',
                        -1 : 'frequency',
                        0  : 'inFine1',
                        1  : 'inFine2',
                        2  : 'inFast3',
                        4  : 'inFast4',
                        20 : 'outA',
                        21 : 'outB',
                        30 : 'outLockIn',
                        31 : 'outPID1',
                        32 : 'outPID2',
                        50 : 'outPiezoVoltage',
                        51 : 'outCCCurrent',
                        52 : 'inCCA',
                        53 : 'inCCB',
                        54 : 'inLaserPD',
                        55 : 'inExtPD',
                        56 : 'outLaserSetTemp',
                        57 : 'inLaserActTemp',
                        60 : 'inAmpCCA',
                        61 : 'inSeedPower',
                        62 : 'inAmpPower',
                        63 : 'outAmpCurrent',
                        70 : 'inCTLLaserPower',
                        80 : 'inSHGCavityErrorSignal',
                        81 : 'inSHGCavityRejectionSignal',
                        82 : 'inSHGIntraCavitySignal',
                        83 : 'inSHGPower',
                        84 : 'inAmpPower',
                        85 : 'inSeedPower',
                        86 : 'inFiberPower',
                        87 : 'inSHGInputPower',
                        90 : 'outSHGCavityPiezoVoltageSlow',
                        91 : 'outSHGCavityPiezoVoltageFast',
                        110 : 'inFHGCavityErrorSignal',
                        111 : 'inFHGCavityRejectionSignal',
                        112 : 'inFHGIntraCavitySignal',
                        113 : 'inFHGPower',
                        120 : 'outFHGCavityPiezoVoltageSlow',
                        121 : 'outFHGCavityPiezoVoltageFast',
                        # aliases
                        100 : 'inLockInput',
                        101 : 'outScanOutputChannel',
                        102 : 'inPowerLockInput'
                       }

    @InterfaceErrorWrapper
    def query(self, cmd, type):
        with Client(NetworkConnection(self.COM_port, timeout = 5)) as client:
            return client.get(cmd, type)

    @InterfaceErrorWrapper
    def set(self, cmd, value):
        with Client(NetworkConnection(self.COM_port, timeout = 5)) as client:
            client.set(cmd, value)
            set = client.get(cmd, type(value))
            if set != value:
                func_name = sys._getframe(1).f_code.co_name
                logging.warning("DLCProCs warning in {0}() : ".format(func_name) \
                                + str(err))
        return

    @checkTypeWrapper(laser = int)
    def laserEmission(self, laser):
        return self.query('laser{0}:emission'.format(laser), bool)

    #######################################################
    # General Laser Commands
    #######################################################
    @checkTypeWrapper(laser = int)
    def grabErrorSignal(self, laser, timescale):
        self.setLaserScopeVariant(laser = laser, variant = 1)
        self.setLaserScopeChannelSignal(laser = laser, channel = 1, signal = 0)
        self.setLaserScopeChannelSignal(laser = laser, channel = 2, signal = 51)
        self.setLaserScopeUpdateRate(laser = 1, update_rate = 1)
        self.setLaserScopeChannelxScopeTimescale(laser = laser, timescale = timescale)

        data = self.query('laser{0}:scope:data'.format(laser), bytes)
        data = extract_float_arrays('xyY', data)
        return data

    #######################################################
    # General Laser Commands
    #######################################################

    @checkTypeWrapper(laser = int)
    def laserProductName(self, laser):
        return self.query('laser{0}:product-name'.format(laser), str)

    @checkTypeWrapper(laser = int)
    def laserEmission(self, laser):
        return self.query('laser{0}:emission'.format(laser), bool)

    @checkTypeWrapper(laser = int)
    def laserType(self, laser):
        return self.query('laser{0}:type'.format(laser), str)

    @checkTypeWrapper(laser = int)
    def laserHealth(self, laser):
        return self.query('laser{0}:health'.format(laser), int)

    @checkTypeWrapper(laser = int)
    def laserHealthTxt(self, laser):
        return self.query('laser{0}:health-txt'.format(laser), str)

    #######################################################
    # Laser Current Controller Commands
    #######################################################

    @checkTypeWrapper(laser = int)
    def laserDlCcEnabled(self, laser):
        return self.query('laser{0}:dl:cc:enabled'.format(laser), bool)

    @checkTypeWrapper(laser = int)
    def laserDlCcEmission(self, laser):
        return self.query('laser{0}:dl:cc:emission'.format(laser), bool)

    @checkTypeWrapper(laser = int)
    def LaserDlCcVariant(self, laser):
        return self.query('laser{0}:dl:cc:variant'.format(laser), str)

    #######################################################
    # Laser Temperature Controller Commands
    #######################################################

    @checkTypeWrapper(laser = int)
    def laserDlTcTempAct(self, laser):
        return self.query('laser{0}:dl:tc:temp-act'.format(laser), float)

    @checkTypeWrapper(laser = int)
    def laserDlTcReady(self, laser):
        return self.query('laser{0}:dl:tc:ready'.format(laser), bool)

    #######################################################
    # Laser Piezo Controller Commands
    #######################################################

    @checkTypeWrapper(laser = int)
    def laserDlPcEnabled(self, laser):
        return self.query('laser{0}:dl:pc:enabled'.format(laser), bool)

    @checkTypeWrapper(laser = int)
    def laserDlPcStatus(self, laser):
        return self.query('laser{0}:dl:pc:status'.format(laser), int)

    @checkTypeWrapper(laser = int)
    def laserDlPCHeatsinkTemp(self, laser):
        return self.query('laser{0}:dl:pc:heatsink-temp'.format(laser), float)

    #######################################################
    # Laser Lock Commands
    #######################################################

    @checkTypeWrapper(laser = int)
    def laserDlLockState(self, laser):
        return self.query('laser{0}:dl:lock:state'.format(laser), int)

    @checkTypeWrapper(laser = int)
    def laserDlLockStateTxt(self, laser):
        return self.query('laser{0}:dl:lock:state-txt'.format(laser), str)

    @checkTypeWrapper(laser = int)
    def laserDlLockEnabled(self, laser):
        return self.query('laser{0}:dl:lock:lock-enabled'.format(laser), bool)

    #######################################################
    # Laser Scope Commands
    #######################################################

    @checkTypeWrapper(laser = int, variant = int)
    def setLaserScopeVariant(self, laser, variant):
        self.set('laser{}:scope:variant'.format(laser), variant)

    @checkTypeWrapper(laser = int)
    def queryLaserScopeVariant(self, laser):
        return self.query('laser{}:scope:variant'.format(laser), int)

    @checkTypeWrapper(laser = int, update_rate = int)
    def setLaserScopeUpdateRate(self, laser, update_rate):
        self.set('laser{}:scope:update-rate'.format(laser), update_rate)

    @checkTypeWrapper(laser = int)
    def queryLaserScopeUpdaterate(self, laser):
        return self.query('laser{}:scope:update-rate'.format(laser), int)

    @checkTypeWrapper(laser = int, channel = int, signal = int)
    def setLaserScopeChannelSignal(self, laser, channel, signal):
        self.set('laser{}:scope:channel{}:signal'.format(laser, channel), signal)

    @checkTypeWrapper(laser = int, channel = int)
    def queryLaserScopeChannelSignal(self, laser, channel):
        return self.query('laser{}:scope:channel{}:signal'.format(laser, channel),
                          int)

    @checkTypeWrapper(laser = int, channel = int)
    def laserScopeChannelUnit(laser, channel):
        return self.query('laser{}:scope:channel{}:name'.format(laser, channel),
                          str)

    @checkTypeWrapper(laser = int, channel =  int)
    def laserScopeChannelName(laser, channel):
        return self.query('laser{}:scope:channel{}:name'.format(laser, channel),
                          str)

    @checkTypeWrapper(laser = int, signal = int)
    def setLaserScopeChannelxXySignal(self, laser, signal):
        self.set('laser{}:scope:channelx:xy-signal'.format(laser), signal)

    @checkTypeWrapper(laser = int)
    def queryLaserScopeChannelxXySignal(self, laser):
        return self.query('laser{}:scope:channelx:xy-signal'.format(laser), int)

    @checkTypeWrapper(laser = int, timescale = (int, float))
    def setLaserScopeChannelxScopeTimescale(self, laser, timescale):
        self.set('laser{}:scope:channelx:scope-timescale'.format(laser), timescale)

    @checkTypeWrapper(laser = int)
    def queryLaserScopeChannelxScopeTimescale(self, laser):
        return self.query('laser{}:scope:channelx:scope-timescale'.format(laser),
                          float)

    @checkTypeWrapper(laser = int, spectrum_range = (int, float))
    def setLaserScopeChannelxSpectrumRange(self, laser, spectrum_range):
        self.set('laser{}:scope:channelx:spectrum-range'.format(laser),
                 spectrum_range)

    @checkTypeWrapper(laser = int)
    def queryLaserScopeChannelxSpectrumRange(self, laser):
        return self.query('laser{}:scope:channelx:spectrum-range'.format(laser),
                          float)

    #######################################################
    # Laser Recorder Commands
    #######################################################

    @checkTypeWrapper(laser = int)
    def laserRecorderState(self, laser):
        return self.query('laser{0}:recorder:state', int)

    @checkTypeWrapper(laser = int)
    def laserRecorderStateTxt(self, laser):
        return self.query('laser{0}:recorder:state-txt', str)

    @checkTypeWrapper(laser = int, channel = int, signal = int)
    def setLaserRecorderSignals(self, laser, channel, signal):
        self.set('laser{0}:recorder:signals:channel{1}'.format(laser, channel),
                   signal)

    @checkTypeWrapper(laser = int, channel = int, signal = int)
    def queryLaserRecorderSignals(self, laser, channel):
        return self.query('laser{0}:recorder:signals:channel{1}'.format(laser,
                          channel), int)

    @checkTypeWrapper(laser = int, time = (int, float))
    def setLaserRecorderRecordingTime(self, laser, time):
        self.set('laser{0}:recorder:recording-time'.format(laser, channel), time)

    @checkTypeWrapper(laser = int)
    def queryLaserRecorderRecordingTime(self, laser):
        return self.query('laser{0}:recorder:recording-time'.format(laser), float)

    @checkTypeWrapper(laser = int, sample_count = int)
    def setLaserRecorderSampleCountSet(self, laser, sample_count):
        self.set('laser{0}:recorder:sample-count-set'.format(laser), sample_count)

    @checkTypeWrapper(laser = int)
    def querylaserRecorderSampleCountSet(self, laser):
        return self.query('laser{0}:recorder:sample-count-set'.format(laser), int)

    @checkTypeWrapper(laser = int)
    def laserRecorderSampleCount(self, laser):
        return self.query('laser{0}:recorder:sample-count'.format(laser), int)

    @checkTypeWrapper(laser = int)
    def laserRecorderSamplingInterval(self, laser):
        return self.query('laser{0}:recorder:sampling-interval'.format(laser), float)

    @checkTypeWrapper(laser = int, channel = int)
    def laserRecorderDataChannelSignal(self, laser, channel):
        return self.query('laser{0}:recorder:data:channel{1}:signal'.format(
                          laser, channel), int)

    @checkTypeWrapper(laser = int, channel = int)
    def laserRecorderDataChannelUnit(self, laser, channel):
        return self.query('laser{0}:recorder:data:channel{1}:unit'.format(laser,
                          channel), str)

    @checkTypeWrapper(laser = int, channel = int)
    def laserRecorderDataChannelName(self, laser, channel):
        return self.query('laser{0}:recorder:data:channel{1}:name'.format(laser,
                          channel), str)

    @checkTypeWrapper(laser = int)
    def laserRecorderDataRecorderSampleCount(self, laser):
        return self.query('laser{0}:recorder:data:recorded-sample-count'.format(laser), int)

    @checkTypeWrapper(laser = int)
    def laserRecorderDataLastValidSample(self, laser):
        return self.query('laser{0}:recorder:data:last-valid-sample')

    @checkTypeWrapper(laser = int, start_index = int, count = int)
    def laserRecorderDataGetData(self, laser, start_index, count):
        data = self.query('laser{0}:recorder:data:get-data'.format(laser), bytes)

    #######################################################
    # Current Controller Board Commands
    #######################################################

    @checkTypeWrapper(cc = int)
    def ccTemp(self, cc):
        return self.query('cc{0}:board-temp'.format(cc), float)

    @checkTypeWrapper(cc = int)
    def ccVariant(self, cc):
        return self.query('cc{0}:variant'.format(cc), str)

    @checkTypeWrapper(cc = int)
    def ccStatus(self, cc):
        return self.query('cc{0}:status'.format(cc), int)

    @checkTypeWrapper(cc = int)
    def ccStatusTxt(self, cc):
        return self.query('cc{0}:status'.format(cc), str)

    #######################################################
    # Temperature Controller Board Commands
    #######################################################

    @checkTypeWrapper(tc = int)
    def tcBoardTemp(self, tc):
        return self.query('tc{0}:board-temp'.format(tc), float)

    #######################################################
    # System Messages Commands
    #######################################################

    def powerSupplyBoardTemp(self):
        return self.query('power-supply:board-temp', float)

    def powerSupplyHeatsinkTemp(self):
        return self.query('power-supply:board-temp', float)

    def powerSupplyType(self):
        return self.query('power-supply:type', str)

    def powerSupplyLoad(self):
        return self.query('power-supply:load', float)

    def powerSupplyStatus(self):
        return self.query('power-supply:status', int)

    def powerSupplyStatusTxt(self):
        return self.query('power-supply:status-txt', str)

    #######################################################
    # System Messages Commands
    #######################################################

    def systemMessagesCount(self):
        return self.query('system-messages:count', int)

    def systemMessagesLatest(self):
        return self.query('system-messages:latest-message', str)

    #######################################################
    # To Organize
    #######################################################

    def mcBoardTemp(self):
        return self.query('mc:board-temp', float)

    def mcRelativeHumidity(self):
        return self.query('mc:realtive-humidity', float)

    def mcAirPressure(self):
        return self.query('mc:air-pressure', float)


if __name__ == "__main__":
    dlc = DLCProCs(0, '172.28.168.181')
    print(dlc.laserProductName(laser = 1))
    print(dlc.tcBoardTemp(tc = 1))
    print(dlc.laserEmission(laser = 1))
