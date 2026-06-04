#include <chrono>
#include <csignal>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

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
bool has_arg(int argc, char* argv[], const std::string& value) {
    for (int i = 1; i < argc; ++i) {
        if (value == argv[i]) {
            return true;
        }
    }
    return false;
}

std::string base64_encode(const unsigned char* data, size_t length) {
    static const char table[] =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string encoded;
    encoded.reserve(((length + 2) / 3) * 4);

    for (size_t i = 0; i < length; i += 3) {
        const unsigned int octet_a = data[i];
        const unsigned int octet_b = (i + 1 < length) ? data[i + 1] : 0;
        const unsigned int octet_c = (i + 2 < length) ? data[i + 2] : 0;
        const unsigned int triple = (octet_a << 16) | (octet_b << 8) | octet_c;

        encoded.push_back(table[(triple >> 18) & 0x3F]);
        encoded.push_back(table[(triple >> 12) & 0x3F]);
        encoded.push_back((i + 1 < length) ? table[(triple >> 6) & 0x3F] : '=');
        encoded.push_back((i + 2 < length) ? table[triple & 0x3F] : '=');
    }

    return encoded;
}
}  // namespace

int main(int argc, char* argv[]) {
    std::signal(SIGINT, handle_signal);
    std::signal(SIGTERM, handle_signal);

    const bool test_mode = has_arg(argc, argv, "--test");

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
            const auto* data = static_cast<const unsigned char*>(converted->GetData());

            if (test_mode) {
                std::cerr << "Frame OK: " << width << "x" << height << " bytes=" << bytes << std::endl;
                image->Release();
                camera->EndAcquisition();
                camera->DeInit();
                camera = nullptr;
                camera_list.Clear();
                system->ReleaseInstance();
                return 0;
            }

            const std::string payload = base64_encode(data, bytes);
            std::cout << "VSSS_FRAME_B64 " << width << " " << height << " "
                      << bytes << " " << payload.size() << "\n";
            std::cout.write(payload.data(), static_cast<std::streamsize>(payload.size()));
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
