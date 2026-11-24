#include "controller.hpp"
#include <iostream>
#include <fstream>
#include <limits>
#include <thread>

void check(bool ok,const char* message) {if(!ok) throw std::runtime_error(message);}
void testsModelo() {
    for(int n:{1000,1001}) {
        Modelo::Vec y(n);
        for(int i=0;i<n;++i)y[i]=2+3*std::sin(2*Modelo::PI*50*i/n);
        auto fm=Modelo::spectrum(y,n);
        check(std::abs(fm.second[0]-2)<1e-10,"DC FFT");check(std::abs(fm.second[50]-3)<1e-10,"Amplitud FFT par/impar");
    }
    Modelo::Vec ny(1000);for(int i=0;i<1000;++i)ny[i]=i%2?-1:1;
    check(std::abs(Modelo::spectrum(ny,1000).second.back()-1)<1e-10,"Nyquist no se duplica");
    for(double z:{0.,.15,.999999999}) {
        auto r=Modelo::oscillator(2.5,z,3.2);check(std::abs(r.x[0]-1)<1e-12 && std::abs(r.v[0]-3.2)<1e-12,"Condiciones iniciales");
    }
    int rechazados=0;
    try{Modelo::signal(500,1000,1);}catch(const std::invalid_argument&){++rechazados;}
    try{Modelo::oscillator(2,1,0);}catch(const std::invalid_argument&){++rechazados;}
    try{Modelo::oscillator(51,.1,0);}catch(const std::invalid_argument&){++rechazados;}
    try{Modelo::oscillator(2,.1,std::numeric_limits<double>::quiet_NaN());}catch(const std::invalid_argument&){++rechazados;}
    check(rechazados==4,"Validaciones defensivas");
    auto s=Modelo::factorize(40);
    check((s.A-s.U*s.s.asDiagonal()*s.Vt).norm()/s.A.norm()<1e-12,"Reconstrucción SVD completa");
    auto a=Modelo::reconstruct(s,1),b=Modelo::reconstruct(s,4);
    check(b.error<=a.error,"Error disminuye con k");
    check(std::abs(b.error-s.s.tail(36).norm()/s.s.norm())<1e-12,"Error Frobenius espectral");
    check(std::abs(b.reduction-79.75)<1e-12,"Reducción de memoria");
    std::cout<<"PRUEBAS MODELO C++: correctas\n";
}
int main(int argc,char** argv) {
    try {
        bool test=argc>1 && std::string(argv[1])=="--test";
        bool ui=argc>1 && std::string(argv[1])=="--test-ui";
        if(test) {testsModelo();return 0;}
        QApplication app(argc,argv);LabView view;Controller controller(view,ui);view.show();
        if(ui) {
            QString dir=argc>2?argv[2]:".";QDir().mkpath(dir);
            auto wait=[&]{QElapsedTimer t;t.start();while(controller.busy() && t.elapsed()<60000){app.processEvents();QThread::msleep(10);}check(!controller.busy(),"Tiempo de espera UI");app.processEvents();};
            wait();check(controller.fftCount()==1 && controller.svdCount()==1,"Cálculo inicial");
            view.scale->setCurrentIndex(1);app.processEvents();check(controller.fftCount()==1,"Escala recalculó FFT");
            view.scale->setCurrentIndex(0);app.processEvents();
            check(view.grab().save(dir+"/cpp_fft.png"),"Captura FFT");
            view.tabs->setCurrentIndex(1);view.velocity->setValue(3);view.simulate->click();app.processEvents();
            check(view.grab().save(dir+"/cpp_oscilador.png"),"Captura oscilador");
            view.zeta->setValue(1);view.simulate->click();check(!controller.lastError.isEmpty(),"No se avisó dominio inválido");
            view.reset->click();check(view.velocity->value()==0 && view.zeta->value()==.15,"Restablecimiento");
            view.tabs->setCurrentIndex(2);view.rank->setValue(7);app.processEvents();check(controller.svdCount()==1,"k recalculó SVD");
            check(view.grab().save(dir+"/cpp_svd.png"),"Captura SVD");
            view.dimension->setCurrentText("250");wait();check(controller.svdCount()==2 && view.rank->value()==1,"Dimensión no invalidó SVD");
            view.freq->setValue(6000);view.generate->click();wait();check(controller.fftCount()==1,"FFT inválida alteró estado");
            std::cout<<"PRUEBAS UI C++: escala sin FFT; rango sin SVD; dimensión recalcula; alertas y reset correctos.\n";return 0;
        }
        return app.exec();
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
