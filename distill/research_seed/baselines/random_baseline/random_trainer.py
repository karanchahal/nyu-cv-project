"""
This file runs the main training/val loop, etc... using Lightning Trainer    
"""
from pytorch_lightning import Trainer
from argparse import ArgumentParser
from research_seed.baselines.random_baseline.random_model import Random_Cifar
from pytorch_lightning.logging import TestTubeLogger
from research_seed.baselines.model.model_factory import create_cnn_model, is_resnet
import torch 
from collections import OrderedDict

def load_model_chk(model, path, num, n):
    chkp = torch.load(path)
    new_state_dict = OrderedDict()
    for k, v in chkp['state_dict'].items():
        if k[:num] == n or n == "x":
            #print(k)
            name = k[num:] # remove `model.`
            new_state_dict[name] = v
    model.load_state_dict(new_state_dict)
    return model

def main(hparams):
    # init module

    # Student
    student = create_cnn_model(hparams.student_model, dataset=hparams.dataset)

    student = load_model_chk(student, hparams.path_to_student, num=8, n="student.")

    # Teacher
    teacher = create_cnn_model(hparams.teacher_model, dataset=hparams.dataset)

    model = Random_Cifar(student, teacher, hparams)
    logger = TestTubeLogger(
       save_dir=hparams.save_dir,
       version=hparams.version # An existing version with a saved checkpoint
    )
    # most basic trainer, uses good defaults
    if hparams.gpus > 1:
      dist = 'ddp'
    else:
      dist = None

    # most basic trainer, uses good defaults
    trainer = Trainer(
        max_nb_epochs=hparams.epochs,
        gpus=hparams.gpus,
        nb_gpu_nodes=hparams.nodes,
        early_stop_callback=None,
        logger=logger,
        default_save_path=hparams.save_dir,
        distributed_backend=dist,
    )

    trainer.fit(model)


if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--epochs', default=100, type=int,  help='number of total epochs to run')
    parser.add_argument('--gpus', type=int, default=1)
    parser.add_argument('--nodes', type=int, default=1)
    parser.add_argument('--save-dir', type=str, default='./lightning_logs')
    parser.add_argument('--version', type=int, required=True, help= "version number for experiment")
    # give the module a chance to add own params
    # good practice to define LightningModule speficic params in the module
    parser = Random_Cifar.add_model_specific_args(parser)

    # parse params
    hparams = parser.parse_args()

    main(hparams)
