#pragma once
#include "models.hpp"
#include "view.hpp"
#include <future>
#include <chrono>
#include <optional>

struct FFTState {Modelo::Signal data;double f=0,fs=0,duration=0;int executions=0;};
struct SVDState {Modelo::SVD data;int dimension=0,executions=0;};

class Controller:public QObject {
    LabView& view;
    std::optional<FFTState> fft;
    std::optional<SVDState> svd;
    std::future<FFTState> fftJob;
    std::future<SVDState> svdJob;
    QTimer timer;
    bool testing;
public:
    QString lastError;
    Controller(LabView& v,bool test=false):view(v),testing(test) {
        connect(view.generate,&QPushButton::clicked,this,[this]{generate();});
        connect(view.scale,QOverload<int>::of(&QComboBox::currentIndexChanged),this,[this]{redrawFFT();});
        connect(view.simulate,&QPushButton::clicked,this,[this]{simulate();});
        connect(view.reset,&QPushButton::clicked,this,[this]{view.natural->setValue(2.5);view.zeta->setValue(.15);view.velocity->setValue(0);simulate();});
        connect(view.dimension,QOverload<int>::of(&QComboBox::currentIndexChanged),this,[this]{factorize();});
        connect(view.rank,&QSlider::valueChanged,this,[this]{redrawSVD();});
        connect(&timer,&QTimer::timeout,this,[this]{collect();});timer.start(20);
        simulate();generate();factorize();
    }
    bool busy()const {return fftJob.valid()||svdJob.valid();}
    int fftCount()const{return fft?fft->executions:0;}
    int svdCount()const{return svd?svd->executions:0;}
    void warn(const std::exception& e) {
        lastError=QString::fromUtf8(e.what());view.status->setText(lastError);
        if(!testing) QMessageBox::warning(&view,"Parámetros o cálculo inválidos",lastError);
    }
    void simulate() {
        try {
            auto r=Modelo::oscillator(view.natural->value(),view.zeta->value(),view.velocity->value());
            view.responsePlot->setData(r.t,r.x,"Respuesta temporal","Tiempo (s)","Desplazamiento");
            view.phasePlot->setData(r.x,r.v,"Retrato de fase","Desplazamiento x","Velocidad v");
            view.status->setText("Oscilador válido · 2 000 muestras · x(0)=1");
        } catch(const std::exception& e) {warn(e);}
    }
    void generate() {
        if(fftJob.valid()) return;
        double f=view.freq->value(),fs=view.fs->value(),d=view.duration->value();
        if(fft && fft->f==f && fft->fs==fs && fft->duration==d) {redrawFFT();return;}
        int count=fftCount();view.generate->setEnabled(false);view.status->setText("Calculando FFT en segundo plano…");
        fftJob=std::async(std::launch::async,[f,fs,d,count]{return FFTState{Modelo::signal(f,fs,d),f,fs,d,count+1};});
    }
    void factorize() {
        if(svdJob.valid()) return;
        int n=view.dimension->currentText().toInt();
        if(svd && n==svd->dimension) {redrawSVD();return;}
        int count=svdCount();view.dimension->setEnabled(false);view.rank->setEnabled(false);
        view.status->setText("Calculando SVD en segundo plano…");
        svdJob=std::async(std::launch::async,[n,count]{return SVDState{Modelo::factorize(n),n,count+1};});
    }
    void collect() {
        if(fftJob.valid() && fftJob.wait_for(std::chrono::seconds(0))==std::future_status::ready) {
            try {fft=fftJob.get();redrawFFT();view.status->setText("FFT guardada en RAM; escala independiente del modelo.");}
            catch(const std::exception& e) {warn(e);}
            view.generate->setEnabled(true);
        }
        if(svdJob.valid() && svdJob.wait_for(std::chrono::seconds(0))==std::future_status::ready) {
            try {
                svd=svdJob.get();QSignalBlocker blocker(view.rank);
                view.rank->setRange(1,svd->dimension/10);view.rank->setValue(1);redrawSVD();
                view.status->setText("SVD guardada en RAM; cambiar k no vuelve a factorizar.");
            } catch(const std::exception& e) {
                if(svd) {QSignalBlocker blocker(view.dimension);view.dimension->setCurrentText(QString::number(svd->dimension));}
                warn(e);
            }
            view.dimension->setEnabled(true);view.rank->setEnabled(true);
        }
    }
    void redrawFFT() {
        if(!fft) return;
        const auto& r=fft->data;
        std::size_t limit=std::min(r.t.size(),static_cast<std::size_t>(std::floor(.02*fft->fs))+1);
        Modelo::Vec t(r.t.begin(),r.t.begin()+limit),y(r.y.begin(),r.y.begin()+limit);
        view.timePlot->setData(t,y,"Ventana inicial (hasta 20 ms)","Tiempo (s)","Amplitud");
        view.fftPlot->setData(r.f,r.m,"Espectro unilateral","Frecuencia (Hz)","Amplitud normalizada",view.scale->currentIndex()==1);
        view.fftLabel->setText(QString("FFT ejecutadas: %1 · La escala reutiliza los resultados. En log se omite DC.").arg(fftCount()));
    }
    void redrawSVD() {
        if(!svd) return;
        try {
            int k=view.rank->value();auto a=Modelo::reconstruct(svd->data,k);
            view.rankLabel->setText(QString("k = %1").arg(k));
            view.errorLabel->setText(QString("Error Frobenius\n%1").arg(a.error,0,'f',4));
            view.reductionLabel->setText(QString("Reducción de almacenamiento\n%1%").arg(a.reduction,0,'f',2));
            view.countLabel->setText(QString("Ejecuciones SVD\n%1").arg(svdCount()));
            Modelo::Vec x(svd->dimension),y(svd->dimension);
            for(int i=0;i<svd->dimension;++i){x[i]=i+1;y[i]=svd->data.s(i);}
            view.svdPlot->setData(x,y,"Decaimiento de valores singulares","Índice","Valor singular (log)",false,true,k);
            view.ramLabel->setText(QString("Reducción teórica al almacenar Uₖ, σₖ y Vᵀₖ. Arreglos completos de la sesión con Aₖ: %1 MiB. Una matriz aleatoria puede conservar un error elevado.").arg(a.bytes/std::pow(2.,20),0,'f',2));
        } catch(const std::exception& e) {warn(e);}
    }
};
