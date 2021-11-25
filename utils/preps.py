from config import GPU_MEMORY_FRACTION


def configure_gpu(device_num: int = 0, memory_fraction: float = GPU_MEMORY_FRACTION):
    import tensorflow as tf
    from keras.backend import set_session

    gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=memory_fraction,
                                          allow_growth=True,
                                          visible_device_list=str(device_num))
    config = tf.compat.v1.ConfigProto(gpu_options=gpu_options)
    config.gpu_options.allow_growth = True
    session = tf.compat.v1.Session(config=config)
    set_session(session)


def select_gpu(answer: str = 'y'):
    """ Print the list of accessible GPU devices and allow to select one(s) """

    from tensorflow.python.client import device_lib
    devices = [d for d in device_lib.list_local_devices() if d.device_type == 'GPU']
    if len(devices) == 0:
        while True:
            answer = answer or input("No GPUs are detected! Would you like to use CPU? [Y/n] ").lower()
            if answer in ["", "y", "n"]:
                break

        if answer == "" or answer == "y":
            print("Using CPU for calculations!")
        else:
            exit(-1)
    else:
        if len(devices) == 1:
            device = devices[0]
            configure_gpu(device.name.rsplit(":", 1)[1], GPU_MEMORY_FRACTION)
        else:
            while True:
                for x in devices:
                    print(x.device_type, x.physical_device_desc)

                cuda_devnum = int(input("Which GPU would you like to use? "))

                if cuda_devnum < 0 or cuda_devnum >= len(devices):
                    continue

                device = devices[cuda_devnum]
                configure_gpu(cuda_devnum, GPU_MEMORY_FRACTION)
                break

        print("Using {}".format(device.name))
