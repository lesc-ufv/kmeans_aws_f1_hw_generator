from veriloggen import *

from make_kmeans_top import make_kmeans_top
from utils import validate_configurations, initialize_regs


class KmeanAcc:
    def __init__(self, external_data_width, data_width, k, dimensions, copies):
        self.external_data_width = external_data_width
        self.data_width = data_width
        self.k = k
        self.dimensions = dimensions
        self.num_in = copies
        self.num_out = copies
        self.copies = copies

    def get_num_in(self):
        return self.num_in

    def get_num_out(self):
        return self.num_out

    def get(self):
        return self.create_kmeans_acc()

    def create_kmeans_acc(self):
        # Verificação do preenchimento total da linha de cache pelo circuito.
        if not validate_configurations(self.external_data_width, self.data_width, self.dimensions):
            print('Erro de geração')
            print('A geração do circuito depende do preenchimento completo da linha de cache fornecida.')
            print('')
            exit(1)

        m = Module('kmeans_acc')

        INTERFACE_DATA_WIDTH = m.Parameter('INTERFACE_DATA_WIDTH', self.external_data_width)

        # sinais básicos para o funcionamento do circuito
        clk = m.Input('clk')
        rst = m.Input('rst')
        start = m.Input('start')

        acc_user_done_rd_data = m.Input('acc_user_done_rd_data',self.num_in)
        acc_user_done_wr_data = m.Input('acc_user_done_wr_data',self.num_out)
        # acc_user_available_read = m.Input('acc_user_available_read')
        acc_user_read_data = m.Input('acc_user_read_data', Mul(self.num_in,self.external_data_width))
        acc_user_request_read = m.Output('acc_user_request_read',self.num_in)
        acc_user_read_data_valid = m.Input('acc_user_read_data_valid',self.num_in)
        acc_user_available_write = m.Input('acc_user_available_write',self.num_out)
        acc_user_write_data = m.Output('acc_user_write_data', Mul(self.num_out,self.external_data_width))
        acc_user_request_write = m.Output('acc_user_request_write',self.num_out)
        acc_user_done = m.Output('acc_user_done')
        kmeans_top_done = m.Wire('kmeans_top_done',self.copies)
        acc_user_done_r = m.Reg('acc_user_done_r')
        start_r = m.Reg('start_r')
        flag = m.Reg('flag')

        acc_user_done.assign(acc_user_done_r)

        m.Always(Posedge(clk))(
            If(rst)(
                acc_user_done_r(Int(0, 1, 2)),
                flag(Int(1, 1, 2)),
                start_r(Int(0, 1, 2))
            ).Else(
                acc_user_done_r(Int(0, 1, 2)),
                If(Uand(kmeans_top_done) & flag & acc_user_done_wr_data)(
                    acc_user_done_r(Int(1, 1, 2)),
                    flag(Int(0, 1, 2))
                ),
                If(start)(
                    start_r(Int(1, 1, 2))
                )
            )
        )

        kmeans = make_kmeans_top(self.external_data_width, self.data_width, self.k, self.dimensions)
        for i in range(self.copies):
            params = []
            con = [('clk', clk), ('rst', rst), ('start', start_r), ('kmeans_top_done_rd_data', acc_user_done_rd_data[i]),
                ('kmeans_top_done_wr_data', acc_user_done_wr_data[i]),
                # ('kmeans_top_available_read', acc_user_available_read),
                ('kmeans_top_read_data', acc_user_read_data[Mul(i,INTERFACE_DATA_WIDTH):Sub(Mul(i+1,INTERFACE_DATA_WIDTH),1)]), ('kmeans_top_request_read', acc_user_request_read[i]),
                ('kmeans_top_read_data_valid', acc_user_read_data_valid[i]),
                ('kmeans_top_available_write', acc_user_available_write[i]),
                ('kmeans_top_write_data', acc_user_write_data[Mul(i,INTERFACE_DATA_WIDTH):Sub(Mul(i+1,INTERFACE_DATA_WIDTH),1)]), ('kmeans_top_request_write', acc_user_request_write[i]),
                ('kmeans_top_done', kmeans_top_done[i])]

            m.Instance(kmeans, 'kmeans_top_%d'%i, params, con)

        initialize_regs(m, {'flag': Int(1, 1, 2)})

        return m
