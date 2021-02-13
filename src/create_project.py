import argparse
import traceback

from veriloggen import *

from create_acc_axi_interface import AccAXIInterface
from kmeans_accelerator import KmeanAcc
from utils import commands_getoutput


def write_file(name, string):
    with open(name, 'w') as fp:
        fp.write(string)
        fp.close()


def create_args():
    parser = argparse.ArgumentParser('create_project -h')
    parser.add_argument('-N', '--dimensions', help='Number of Kmeans dimensions', type=int)
    parser.add_argument('-K', '--centroids', help='Number of Kmeans clusters', type=int)
    parser.add_argument('-p', '--name', help='Project name', type=str, default='a.prj')
    parser.add_argument('-o', '--output', help='Project location', type=str, default='.')

    return parser.parse_args()


def main():
    args = create_args()
    running_path = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    kmeans_root = os.getcwd() + '/../'

    if args.output == '.':
        args.output = running_path
        
    if args.dimensions and args.centroids:
        kmeansacc = KmeanAcc(512, 16, [args.centroids], args.dimensions)

        acc_axi = AccAXIInterface(kmeansacc).create_kernel_top()

        commands_getoutput('cp -r %s/resources/template.prj %s/%s' % (kmeans_root, args.output, args.name))

        acc_axi.to_verilog('%s/%s/xilinx_aws_f1/hw/src/kernel_top.v' % (args.output, args.name))

        write_file('%s/%s/xilinx_aws_f1/hw/simulate/num_m_axis.mk' % (args.output, args.name),
                   'NUM_M_AXIS=%d' % kmeansacc.get_num_in())
        write_file('%s/%s/xilinx_aws_f1/hw/synthesis/num_m_axis.mk' % (args.output, args.name),
                   'NUM_M_AXIS=%d' % kmeansacc.get_num_in())
        write_file('%s/%s/xilinx_aws_f1/hw/synthesis/prj_name' % (args.output, args.name), args.name)
        commands_getoutput(
            'rm -rf %s/src/parser.out %s/src/parsetab.py %s/src/__pycache__' % (kmeans_root, kmeans_root, kmeans_root))

        commands_getoutput(
            'rm -rf %s/src/parser.out %s/src/parsetab.py %s/src/__pycache__' % (kmeans_root, kmeans_root, kmeans_root))

        print('Project successfully created in %s/%s' % (args.output, args.name))
    else:
        raise Exception('Missing parameters. Run create_project -h to see all parameters needed')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        traceback.print_exc()
