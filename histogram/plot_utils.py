def add_plot_options(parser):
    parser.add_argument('--xlabel', type=str, nargs=1, help='Histogram x-axis label', required=True)
    parser.add_argument('--ylabel', type=str, nargs=1, help='Histogram y-axis label', required=True)
    parser.add_argument('--title', type=str, nargs=1, help='Histogram title', required=True)
    parser.add_argument('--fname', type=str, nargs=1, help='File name', required=True)
