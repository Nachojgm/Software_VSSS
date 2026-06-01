#include <chrono>
#include <csignal>
#include <iostream>
#include <string>
#include <thread>

#include "Spinnaker.h"

using namespace Spinnaker;
using namespace Spinnaker::GenApi;

namespace {
volatile std::sig_atomic_t g_running = 1;

void handle_signal(int) {
    g_running = 0;
}

void set_continuous_acquisition(CameraPtr camera) {
    INodeMap& node_map = camera->GetNodeMap();
    CEnumerationPtr acquisition_mode = node_map.GetNode("AcquisitionMode");
    if (!IsReadable(acquisition_mode) || !IsWritable(acquisition_mode)) {
        return;
    }

    CEnumEntryPtr continuous = acquisition_mode->GetEntryByName("Continuous");
    if (IsReadable(continuous)) {
        acquisition_mode->SetIntValue(continuous->GetValue());
    }
}
}  // namespace

int main() {
    std::signal(SIGINT, handle_signal);
    std::signal(SIGTERM, handle_signal);

    SystemPtr system = nullptr;
    CameraList camera_list;
    CameraPtr camera = nullptr;

    try {
        system = System::GetInstance();
        camera_list = system->GetCameras();

        if (camera_list.GetSize() == 0) {
            std::cerr << "No se encontro ninguna camara Spinnaker/GigE." << std::endl;
            camera_list.Clear();
            system->ReleaseInstance();
            return 2;
        }

        camera = camera_list.GetByIndex(0);
        camera->Init();
        set_continuous_acquisition(camera);

        ImageProcessor processor;
        processor.SetColorProcessing(SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR);

        camera->BeginAcquisition();
        std::cerr << "Spinnaker bridge listo." << std::endl;

        while (g_running) {
            ImagePtr image = camera->GetNextImage(1000);
            if (!image || image->IsIncomplete()) {
                if (image) {
                    image->Release();
                }
                continue;
            }

            ImagePtr converted = processor.Convert(image, PixelFormat_BGR8);
            const size_t width = converted->GetWidth();
            const size_t height = converted->GetHeight();
            const size_t bytes = width * height * 3;
            const char* data = static_cast<const char*>(converted->GetData());

            std::cout << "VSSS_FRAME " << width << " " << height << " " << bytes << "\n";
            std::cout.write(data, static_cast<std::streamsize>(bytes));
            std::cout << "\n";
            std::cout.flush();

            image->Release();
        }

        camera->EndAcquisition();
        camera->DeInit();
        camera = nullptr;
        camera_list.Clear();
        system->ReleaseInstance();
        return 0;
    } catch (const Spinnaker::Exception& exc) {
        std::cerr << "Spinnaker error: " << exc.what() << std::endl;
    } catch (const std::exception& exc) {
        std::cerr << "Error: " << exc.what() << std::endl;
    }

    try {
        if (camera && camera->IsInitialized()) {
            camera->DeInit();
        }
        camera_list.Clear();
        if (system) {
            system->ReleaseInstance();
        }
    } catch (...) {
    }

    return 1;
}
