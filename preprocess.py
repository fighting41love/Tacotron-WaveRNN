import argparse
import os
from multiprocessing import cpu_count

from datasets import preprocessor
from hparams import hparams
from tqdm import tqdm
from wavernn.preprocess import wavernn_preprocess


def write_metadata(metadata, out_dir):
    with open(os.path.join(out_dir, 'train.txt'), 'w', encoding='utf-8') as f:
        for m in metadata:
            f.write('|'.join([str(x) for x in m]) + '\n')

    mel_frames = sum([int(m[4]) for m in metadata])
    timesteps = sum([int(m[3]) for m in metadata])
    hours = timesteps / hparams.sample_rate / 3600

    print('Write {} utterances, {} mel frames, {} audio timesteps, ({:.2f} hours)'.format(len(metadata), mel_frames, timesteps, hours))
    print('Max input length (text chars): {}'.format(max(len(m[5]) for m in metadata)))
    print('Max mel frames length: {}'.format(max(int(m[4]) for m in metadata)))
    print('Max audio timesteps length: {}'.format(max(m[3] for m in metadata)))


def norm_data(args):
    supported_datasets = ['LJSpeech-1.0', 'LJSpeech-1.1', 'M-AILABS']
    if args.dataset not in supported_datasets:
        raise ValueError('dataset value entered {} does not belong to supported datasets: {}'.format(args.dataset, supported_datasets))

    if args.dataset.startswith('LJSpeech'):
        return [os.path.join(args.base_dir, args.dataset)]

    if args.dataset == 'M-AILABS':
        supported_languages = ['en_US', 'en_UK', 'fr_FR', 'it_IT', 'de_DE', 'es_ES', 'ru_RU',
                               'uk_UK', 'pl_PL', 'nl_NL', 'pt_PT', 'fi_FI', 'se_SE', 'tr_TR', 'ar_SA']
        if args.language not in supported_languages:
            raise ValueError('Please enter a supported language to use from M-AILABS dataset! \n{}'.format(supported_languages))

        supported_voices = ['female', 'male', 'mix']
        if args.voice not in supported_voices:
            raise ValueError('Please enter a supported voice option to use from M-AILABS dataset! \n{}'.format(supported_voices))

        path = os.path.join(args.base_dir, args.language, 'by_book', args.voice)
        supported_readers = [e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e))]
        if args.reader not in supported_readers:
            raise ValueError('Please enter a valid reader for your language and voice settings! \n{}'.format(supported_readers))

        path = os.path.join(path, args.reader)
        supported_books = [e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e))]

        if args.merge_books:
            return [os.path.join(path, book) for book in supported_books]

        else:
            if args.book not in supported_books:
                raise ValueError('Please enter a valid book for your reader settings! \n{}'.format(supported_books))

            return [os.path.join(path, args.book)]


def preprocess(args, hparams):
    input_dir = norm_data(args)
    output_dir = os.path.join(args.base_dir, 'training_data')

    mel_dir = os.path.join(output_dir, 'mels')
    wav_dir = os.path.join(output_dir, 'audio')
    linear_dir = os.path.join(output_dir, 'linear')
    os.makedirs(mel_dir, exist_ok=True)
    os.makedirs(wav_dir, exist_ok=True)
    os.makedirs(linear_dir, exist_ok=True)

    metadata = preprocessor.build_from_path(hparams, input_dir, mel_dir, linear_dir, wav_dir, args.n_jobs, tqdm=tqdm)
    write_metadata(metadata, output_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', default='')
    parser.add_argument('--hparams', default='', help='Hyperparameter overrides as a comma-separated list of name=value pairs')
    parser.add_argument('--model', default='Tacotron')
    parser.add_argument('--dataset', default='LJSpeech-1.1')
    parser.add_argument('--language', default='en_US')
    parser.add_argument('--voice', default='female')
    parser.add_argument('--reader', default='mary_ann')
    parser.add_argument('--merge_books', type=bool, default=False)
    parser.add_argument('--book', default='northandsouth')
    parser.add_argument('--n_jobs', type=int, default=cpu_count())
    args = parser.parse_args()

    accepted_models = ['Tacotron', 'WaveRNN']

    if args.model not in accepted_models:
        raise ValueError('please enter a valid model to train: {}'.format(accepted_models))

    modified_hp = hparams.parse(args.hparams)

    if args.model == 'Tacotron':
        preprocess(args, modified_hp)
    else:
        wavernn_preprocess(args, modified_hp)


if __name__ == '__main__':
    main()
