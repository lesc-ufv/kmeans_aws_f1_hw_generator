from math import ceil, log2

from veriloggen import *

from utils import initialize_regs


class Components:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.cache = {}

    def create_add(self):
        name = 'm_add'
        if name in self.cache.keys():
            return self.cache[name]

        m = Module(name)

        data_width = m.Parameter('DATA_WIDTH', 16)
        centroid_id_width = m.Parameter('CENTROID_ID_WIDTH', 8)

        clk = m.Input('clk')
        rst = m.Input('rst')
        data_in_0 = m.Input('data_in_0', data_width)
        data_in_1 = m.Input('data_in_1', data_width)
        data_out = m.OutputReg('data_out', data_width)

        m.EmbeddedCode('//Separation of the centroid ID values from the data to be processed')
        data_0 = m.Wire('data_0', data_width - centroid_id_width)
        data_1 = m.Wire('data_1', data_width - centroid_id_width)
        centroid_id = m.Wire('centroid_id', centroid_id_width)

        m.EmbeddedCode(' ')
        m.EmbeddedCode('//Assigns')
        data_0.assign(data_in_0[0:data_width - centroid_id_width])
        data_1.assign(data_in_1[0:data_width - centroid_id_width])
        centroid_id.assign(data_in_0[data_width - centroid_id_width:data_width])

        m.Always(Posedge(clk))(
            If(rst)(
                data_out(0),
            ).Else(
                data_out(Cat(centroid_id, (data_0 + data_1))),
            )
        )

        initialize_regs(m)
        self.cache[name] = m

        return m

    def create_cmp(self):
        name = 'm_comp'
        if name in self.cache.keys():
            return self.cache[name]

        m = Module(name)

        data_width = m.Parameter('DATA_WIDTH', 16)
        centroid_id_width = m.Parameter('CENTROID_ID_WIDTH', 8)
        clk = m.Input('clk')
        rst = m.Input('rst')
        data_in_0 = m.Input('data_in_0', data_width)
        data_in_1 = m.Input('data_in_1', data_width)
        data_out = m.OutputReg('data_out', data_width)

        m.EmbeddedCode('//Separation of the centroid ID values from the data to be processed')
        data_0 = m.Wire('data_0', data_width - centroid_id_width)
        data_1 = m.Wire('data_1', data_width - centroid_id_width)
        centroid_id_0 = m.Wire('centroid_id_0', centroid_id_width)
        centroid_id_1 = m.Wire('centroid_id_1', centroid_id_width)

        m.EmbeddedCode(' ')
        m.EmbeddedCode('//Assigns')
        data_0.assign(data_in_0[0:data_width - centroid_id_width])
        data_1.assign(data_in_1[0:data_width - centroid_id_width])
        centroid_id_0.assign(data_in_0[data_width - centroid_id_width:data_width])
        centroid_id_1.assign(data_in_1[data_width - centroid_id_width:data_width])

        m.Always(Posedge(clk))(
            If(rst)(
                data_out(0),
            ).Else(
                data_out(Mux(data_0 < data_1, Cat(centroid_id_0, data_0), Cat(centroid_id_1, data_1))),
            )
        )

        initialize_regs(m)
        self.cache[name] = m

        return m

    def create_imm(self):
        name = 'm_imm'
        if name in self.cache.keys():
            return self.cache[name]

        m = Module(name)

        data_width = m.Parameter('DATA_WIDTH', 16)
        centroid_id_width = m.Parameter('CENTROID_ID_WIDTH', 8)
        centroid_id = m.Parameter('CENTROID_ID', 0)
        imm_id_width = m.Parameter('IMM_ID_WIDTH', 8)
        IMM_ID = m.Parameter('IMM_ID', 0)
        configuration_id_width = m.Parameter('CONF_ID_WIDTH', 32)

        clk = m.Input('clk')
        rst = m.Input('rst')
        centroid_configuration_in = m.Input('centroid_configuration_in', 64)
        data_out = m.Output('data_out', data_width)

        immediate = m.Reg('immediate', data_width - centroid_id_width)

        m.EmbeddedCode(' ')
        m.EmbeddedCode('//Output assign')

        data_out.assign(Cat(centroid_id, immediate))

        m.Always(Posedge(clk))(
            If(rst)(
                immediate(0),
            ).Else(
                If(centroid_configuration_in[0:imm_id_width] == IMM_ID)(
                    immediate(centroid_configuration_in[
                              configuration_id_width:configuration_id_width + data_width - centroid_id_width])
                ),
            )
        )

        initialize_regs(m)
        self.cache[name] = m

        return m

    def create_quad(self):
        name = 'm_quad'
        if name in self.cache.keys():
            return self.cache[name]

        m = Module(name)

        data_width_in = m.Parameter('DATA_WIDTH_IN', 16)
        data_width_out = m.Parameter('DATA_WIDTH_OUT', 16)
        centroid_id_width = m.Parameter('CENTROID_ID_WIDTH', 8)

        clk = m.Input('clk')
        rst = m.Input('rst')
        data_in_0 = m.Input('data_in_0', data_width_in + centroid_id_width)
        data_out = m.OutputReg('data_out', data_width_out)

        m.EmbeddedCode('//Separation of the centroid ID values from the data to be processed')
        data_0 = m.Wire('data_0', data_width_in * 2)
        centroid_id = m.Wire('centroid_id', centroid_id_width)

        m.EmbeddedCode(' ')
        m.EmbeddedCode('//Assigns')

        data_0.assign(Cat(Repeat(data_in_0[data_width_in - 1], data_width_in), data_in_0[0:data_width_in]))

        centroid_id.assign(data_in_0[data_width_in:data_width_in + centroid_id_width])

        m.Always(Posedge(clk))(
            If(rst)(
                data_out(0),
            ).Else(
                data_out(
                    Cat(centroid_id, Repeat(Int(0, 1, 2), (data_width_out - (data_width_in * 2) - centroid_id_width)),
                        (data_0 * data_0))),
            )
        )

        initialize_regs(m)
        self.cache[name] = m
        return m

    def create_reg(self):
        name = 'm_reg'
        if name in self.cache.keys():
            return self.cache[name]

        m = Module(name)

        data_width = m.Parameter('DATA_WIDTH', 16)
        clk = m.Input('clk')
        rst = m.Input('rst')
        data_in_0 = m.Input('data_in_0', data_width)
        data_out = m.OutputReg('data_out', data_width)

        m.Always(Posedge(clk))(
            If(rst)(
                data_out(0),
            ).Else(
                data_out(data_in_0),
            )
        )

        initialize_regs(m)
        self.cache[name] = m

        return m

    def create_sub(self):
        name = 'm_sub'
        if name in self.cache.keys():
            return self.cache[name]

        m = Module(name)

        data_width = m.Parameter('DATA_WIDTH', 16)
        centroid_id_width = m.Parameter('CENTROID_ID_WIDTH', 8)
        clk = m.Input('clk')
        rst = m.Input('rst')
        data_in_0 = m.Input('data_in_0', data_width)
        data_in_1 = m.Input('data_in_1', data_width)
        data_out = m.OutputReg('data_out', data_width)

        m.EmbeddedCode('//Separation of the centroid ID values from the data to be processed')
        data_0 = m.Wire('data_0', data_width - centroid_id_width)
        data_1 = m.Wire('data_1', data_width - centroid_id_width)
        centroid_id = m.Wire('centroid_id', centroid_id_width)

        m.EmbeddedCode(' ')
        m.EmbeddedCode('//Assigns')
        data_0.assign(data_in_0[0:data_width - centroid_id_width])
        data_1.assign(data_in_1[0:data_width - centroid_id_width])
        centroid_id.assign(
            data_in_0[data_width - centroid_id_width:data_width] | data_in_1[data_width - centroid_id_width:data_width])

        m.Always(Posedge(clk))(
            If(rst)(
                data_out(0),
            ).Else(
                data_out(Cat(centroid_id, (data_0 - data_1))),
            )
        )

        initialize_regs(m)
        self.cache[name] = m

        return m

    def create_config_centroids(self, external_data_width):
        name = 'config_centroids'
        if name in self.cache.keys():
            return self.cache[name]

        m = Module('config_centroids')

        # sinais básicos para o funcionamento do circuito
        clk = m.Input('clk')
        rst = m.Input('rst')
        start = m.Input('start')

        # config_centroids_available_read = m.Input('config_centroids_available_read')
        config_centroids_read_data = m.Input('config_centroids_read_data', external_data_width)
        config_centroids_request_read = m.OutputReg('config_centroids_request_read')
        config_centroids_read_data_valid = m.Input('config_centroids_read_data_valid')

        config_centroids_start_circuit = m.OutputReg('config_centroids_start_circuit')
        config_centroids_configurations_out = m.OutputReg('config_centroids_configurations_out', 64)

        m.EmbeddedCode('//For Config Control')
        fsm_config = m.Reg('fsm_config', 3)
        FSM_IDLE_CONF = m.Localparam('FSM_IDLE_CONF', Int(0, fsm_config.width, 10))
        FSM_READ_NUM_CONF = m.Localparam('FSM_READ_NUM_CONF', Int(1, fsm_config.width, 10))
        FSM_READ_CONF = m.Localparam('FSM_READ_CONF', Int(2, fsm_config.width, 10))
        FSM_CONFIGURE = m.Localparam('FSM_CONFIGURE', Int(3, fsm_config.width, 10))
        FSM_CONF_FINISHED = m.Localparam('FSM_CONF_FINISHED', Int(4, fsm_config.width, 10))

        m.EmbeddedCode(' ')
        data_received = m.Reg('data_received', external_data_width)
        counter_end_line = m.Reg('counter_end_line', 9)
        counter_configurations = m.Reg('counter_configurations', 32)
        num_configurations = m.Reg('num_configurations', 32)

        # confControl
        m.EmbeddedCode('//confControl')

        m.Always(Posedge(clk))(
            If(rst)(
                config_centroids_start_circuit(Int(0, 1, 10)),
                config_centroids_request_read(Int(0, 1, 10)),
                config_centroids_configurations_out(Int(0, config_centroids_configurations_out.width, 10)),
                data_received(Int(0, data_received.width, 10)),
                counter_end_line(Int(0, counter_end_line.width, 10)),
                counter_configurations(Int(0, counter_configurations.width, 10)),
                num_configurations(Int(0, num_configurations.width, 10)),
                fsm_config(FSM_IDLE_CONF),
            ).Else(
                config_centroids_request_read(Int(0, 1, 2)),
                Case(fsm_config)(
                    When(FSM_IDLE_CONF)(
                        If(start)(
                            fsm_config(FSM_READ_NUM_CONF),
                        )
                    ),
                    When(FSM_READ_NUM_CONF)(
                        If(config_centroids_read_data_valid)(
                            num_configurations(config_centroids_read_data[0:num_configurations.width]),
                            config_centroids_request_read(Int(1, 1, 2)),
                            fsm_config(FSM_READ_CONF)
                        )
                    ),
                    When(FSM_READ_CONF)(
                        If(counter_configurations >= num_configurations)(
                            fsm_config(FSM_CONF_FINISHED)
                        ).Elif(config_centroids_read_data_valid & ~config_centroids_request_read)(
                            data_received(config_centroids_read_data),
                            config_centroids_request_read(Int(1, 1, 2)),
                            counter_end_line(Int(0, counter_end_line.width, 10)),
                            fsm_config(FSM_CONFIGURE)
                        )
                    ),
                    When(FSM_CONFIGURE)(
                        config_centroids_configurations_out(data_received[0: 64]),
                        data_received(data_received >> Int(64, 10, 10)),
                        counter_end_line(counter_end_line + Int(1, counter_end_line.width, 2)),
                        counter_configurations(counter_configurations + Int(1, counter_configurations.width, 2)),
                        If(counter_end_line == Int((external_data_width // (64)) - 1, counter_end_line.width, 10))(
                            fsm_config(FSM_READ_CONF),
                        ).Else(
                            fsm_config(FSM_CONFIGURE),
                        ),
                    ),
                    When(FSM_CONF_FINISHED)(
                        config_centroids_configurations_out(Int(0, config_centroids_configurations_out.width, 10)),
                        config_centroids_start_circuit(Int(1, 1, 2)),
                        fsm_config(FSM_CONF_FINISHED),
                    ),
                )
            )
        )

        initialize_regs(m, {'fsm_config': FSM_IDLE_CONF})
        self.cache[name] = m

        return m

    def create_input_controller(self, external_data_width):
        name = 'input_controller'
        if name in self.cache.keys():
            return self.cache[name]

        m = Module(name)

        # sinais básicos para o funcionamento do circuito
        clk = m.Input('clk')
        rst = m.Input('rst')
        start = m.Input('start')
        done_rd_data = m.Input('done_rd_data')

        # fifo_in control
        input_controller_read_data = m.Input('input_controller_read_data', external_data_width)
        input_controller_read_data_valid = m.Input('input_controller_read_data_valid')
        input_controller_request_read = m.OutputReg('input_controller_request_read')

        # output
        input_controller_data_out = m.OutputReg('input_controller_data_out', external_data_width)
        input_controller_output_valid = m.OutputReg('input_controller_output_valid', 2)

        m.EmbeddedCode(' ')
        fsm_main = m.Reg('fsm_main', 3)
        FSM_IDLE = m.Localparam('FSM_IDLE', Int(0, fsm_main.width, 10))
        FSM_READ = m.Localparam('FSM_READ', Int(1, fsm_main.width, 10))
        FSM_DONE = m.Localparam('FSM_DONE', Int(2, fsm_main.width, 10))

        m.EmbeddedCode(' ')
        m.Always(Posedge(clk))(
            If(rst)(
                input_controller_data_out(Int(0, input_controller_data_out.width, 10)),
                input_controller_request_read(Int(0, 1, 2)),
                input_controller_output_valid(Int(0, input_controller_output_valid.width, 10)),
                fsm_main(FSM_IDLE),
            ).Else(
                input_controller_request_read(Int(0, 1, 2)),
                input_controller_output_valid(Int(0, input_controller_output_valid.width, 10)),
                Case(fsm_main)(
                    When(FSM_IDLE)(
                        If(start)(
                            fsm_main(FSM_READ),
                        )
                    ),
                    When(FSM_READ)(
                        If(input_controller_read_data_valid)(
                            input_controller_data_out(input_controller_read_data),
                            input_controller_request_read(Int(1, 1, 2)),
                            input_controller_output_valid(Int(1, input_controller_data_out.width, 10))
                        ).Elif(done_rd_data)(
                            fsm_main(FSM_DONE)
                        )
                    ),
                    When(FSM_DONE)(
                        input_controller_output_valid(Int(2, input_controller_data_out.width, 10)),
                        fsm_main(FSM_DONE),
                    ),
                )
            )
        )

        initialize_regs(m, {'fsm_main': FSM_IDLE})
        self.cache[name] = m
        return m

    def create_output_controller(self, external_data_width, data_width, dimensions):

        name = 'output_controller_%d_%d_%d' % (external_data_width, data_width, dimensions)

        if name in self.cache.keys():
            return self.cache[name]

        m = Module(name)

        controller_data_width = 8
        num_inputs = (external_data_width // data_width) // dimensions

        # basic signals BEGIN
        clk = m.Input('clk')
        rst = m.Input('rst')
        start = m.Input('start')
        # basic signals END

        # fifo_out control BEGIN [1-1:0] acc_user_wr_en,
        output_controller_available_write = m.Input('output_controller_available_write')
        output_controller_request_write = m.OutputReg('output_controller_request_write')
        output_controller_write_data = m.OutputReg('output_controller_write_data', external_data_width)
        # fifo_out control END

        # inputdata BEGIN
        output_controller_input_valid = m.Input('output_controller_input_valid', 2)
        output_controller_data_in = m.Input('output_controller_data_in', controller_data_width * num_inputs)
        # inputdata END

        # DONE signal
        output_controller_done = m.OutputReg('output_controller_done')

        if (external_data_width == controller_data_width * num_inputs):
            m.Always(Posedge(clk))(
                If(rst)(
                    output_controller_request_write(Int(0, 1, 2)),
                    output_controller_done(Int(0, 1, 2)),
                ).Elif(AndList(start, Not(output_controller_done)))(
                    EmbeddedCode('//Stop = 00, Done = 10, Valid = 01'),
                    output_controller_request_write(Int(0, 1, 10)),
                    If(output_controller_available_write)(
                        Case(output_controller_input_valid)(
                            When(Int(2, output_controller_input_valid.width, 10))(  # Done = 2
                                output_controller_done(Int(1, 1, 10)),
                            ),
                            When(Int(1, output_controller_input_valid.width, 10))(  # Valid = 1
                                output_controller_write_data(output_controller_data_in),
                                output_controller_request_write(Int(1, 1, 10)),
                            )
                        )
                    )
                )
            )
        else:
            m.EmbeddedCode(" ")
            data = m.Reg('data', external_data_width)
            counter = m.Reg('counter', 10)
            wr_flag = m.Reg("wr_flag")

            m.Always(Posedge(clk))(
                If(rst)(
                    output_controller_request_write(Int(0, 1, 10)),
                    counter(Int(0, counter.width, 10)),
                    data(Int(0, data.width, 10)),
                    output_controller_write_data(Int(0, output_controller_write_data.width, 10)),
                    wr_flag(Int(0, 1, 10)),
                    output_controller_done(Int(0, 1, 10)),
                ).Elif(AndList(start, Not(output_controller_done)))(
                    EmbeddedCode('//Stop = 00, Done = 10, Valid = 01'),
                    output_controller_request_write(Int(0, 1, 10)),
                    If(output_controller_available_write)(
                        Case(output_controller_input_valid)(
                            When(Int(2, 2, 10))(  # Done = 2
                                If(counter >= Int((external_data_width // (controller_data_width * num_inputs)) - 1,
                                                  counter.width,
                                                  10))(
                                    counter(Int(0, counter.width, 10)),
                                    output_controller_write_data(
                                        Cat(output_controller_data_in,
                                            data[controller_data_width * num_inputs:external_data_width])),
                                    output_controller_request_write(Int(1, 1, 10)),
                                    wr_flag(Int(1, 1, 10)),
                                ).Elif(OrList(wr_flag, counter == Int(0, counter.width, 10)))(
                                    output_controller_done(Int(1, 1, 10)),
                                ).Else(
                                    counter(counter + Int(1, counter.width, 10)),
                                    data(Cat(Int(0, controller_data_width * num_inputs, 10),
                                             data[controller_data_width * num_inputs:external_data_width])),
                                ),
                            ),
                            When(Int(1, 2, 10))(  # Valid = 1
                                If(counter >= Int((external_data_width // (controller_data_width * num_inputs)) - 1,
                                                  counter.width,
                                                  10))(
                                    counter(Int(0, counter.width, 10)),
                                    output_controller_write_data(
                                        Cat(output_controller_data_in,
                                            data[controller_data_width * num_inputs:external_data_width])),
                                    data(Int(0, data.width, 10)),
                                    output_controller_request_write(Int(1, 1, 10)),
                                ).Else(
                                    counter(counter + Int(1, counter.width, 10)),
                                    data(Cat(output_controller_data_in,
                                             data[controller_data_width * num_inputs:external_data_width])),
                                ),
                            )
                        )
                    )
                )
            )

        initialize_regs(m)
        self.cache[name] = m

        return m

    def create_validity_protractor(self, k, dimensions):

        name = 'validity_protractor'
        if name in self.cache.keys():
            return self.cache[name]

        m = Module(name)

        # ceil(log2(k)) = reduce min
        # +1 = quad
        # +1 = sub
        # ceil(log2(dimensions)) = reduce ADD
        # (0 if k < 3 else ceil(log2(k)) - 1) = regs
        dfg_depth = ceil(log2(k)) + 2 + ceil(log2(dimensions)) + (0 if k < 3 else ceil(log2(k)) - 1)

        clk = m.Input('clk')
        rst = m.Input('rst')

        validity_protractor_input_valid = m.Input('validity_protractor_input_valid', 2)
        validity_protractor_output_valid = m.OutputReg('validity_protractor_output_valid', 2)

        m.EmbeddedCode(' ')
        m.EmbeddedCode('//Transfer of data validity control signals.')
        valid = m.Reg('valid', dfg_depth * 2)
        # validity_protractor_output_valid.assign(valid[0:2]),

        m.Always(Posedge(clk))(
            If(rst)(
                valid(Int(0, valid.width, 10)),
                validity_protractor_output_valid(Int(0, validity_protractor_output_valid.width, 10)),
            ).Else(
                valid(Cat(validity_protractor_input_valid, valid[2:valid.width])),
                validity_protractor_output_valid(valid[0:2]),
            )
        )

        initialize_regs(m)
        self.cache[name] = m

        return m
