import pathlib
import collections
import logging
import os
import sys
from PIL import Image
import streamlit as st
from time import perf_counter

sys.path.insert(0, f"{os.getcwd()}")
sys.path.insert(0, f"{os.getcwd()}/ada_lib")

from tl2.launch.launch_utils import global_cfg, TLCfgNode, set_global_cfg
from tl2.proj.logger.logger_utils import get_file_logger
from tl2.proj.logger import logging_utils_v2
from tl2.proj.streamlit import st_utils
from tl2.proj.argparser import argparser_utils
from tl2.proj.pytorch import torch_utils


class STModel(object):
  def __init__(self):

    pass

  def projector_web(self,
                    cfg,
                    outdir,
                    **kwargs):

    image_list_kwargs = collections.defaultdict(dict)
    for k, v in cfg.image_list_files.items():
      data_k = k
      image_path = st_utils.parse_image_list(image_list_file=v.image_list_file, header=data_k, )
      image_list_kwargs[data_k]['image_path'] = image_path
    data_k = list(image_list_kwargs.keys())[0]
    image_path = image_list_kwargs[data_k]['image_path']

    # ****************************************************************************

    loss_cfg = cfg.loss_cfg['vgg16_conv_r1024_loss_cfg']
    downsampling_option = st_utils.radio('Options', options=['Downsampling (artifacts)', 'No downsampling'], sidebar=True)

    if downsampling_option == 'Downsampling (artifacts)':
      loss_cfg.downsample_size = 256

    if not global_cfg.tl_debug:
      if not st.sidebar.button("run_web"):
        return

    # ****************************************************************************

    # np.random.seed(seed)
    # torch.manual_seed(seed)
    torch_utils.init_seeds(seed=303, rank=0)

    from exp2.hrinversion.models.projector import StyleGAN2Projector

    projector = StyleGAN2Projector(
      network_pkl=cfg.network_pkl.FFHQ_r1024,
      loss_cfg=loss_cfg)

    start_time = perf_counter()
    projector.project_wplus(
      outdir=outdir,
      image_path=image_path,
      st_web=True,
      **cfg
    )
    print(f'Elapsed: {(perf_counter() - start_time):.1f} s')

    pass


def main(cfg_file,
         command,
         outdir,
         debug=False):

  cfg = TLCfgNode.load_yaml_with_command(cfg_filename=cfg_file, command=command)
  cfg.tl_debug = debug
  set_global_cfg(cfg)

  # outdir
  kwargs = {}
  kwargs['outdir'] = outdir
  os.makedirs(outdir, exist_ok=True)

  get_file_logger(filename=f"{outdir}/log.txt", logger_names=['st'])
  logging_utils_v2.get_logger(filename=f"{outdir}/log.txt")
  logger = logging.getLogger('tl2')
  # logger.info(f"global_cfg:\n{global_cfg.dump()}")

  st_model = STModel()

  st_model.projector_web(cfg=global_cfg.get('projector_web', {}), **kwargs)

  pass

if __name__ == '__main__':

  parser = argparser_utils.get_parser()

  argparser_utils.add_argument_str(parser, name="cfg_file", default="")
  argparser_utils.add_argument_str(parser, name="command", default="projector_web")
  argparser_utils.add_argument_str(parser, name="outdir", default="results")
  argparser_utils.add_argument_bool(parser, name='debug', default=False)

  args, _ = parser.parse_known_args()
  argparser_utils.print_args(args)

  main(**vars(args))
