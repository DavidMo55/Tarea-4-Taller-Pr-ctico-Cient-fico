#pragma once
#include <Eigen/Dense>
#include <unsupported/Eigen/FFT>
#include <cmath>
#include <complex>
#include <random>
#include <stdexcept>
#include <vector>
namespace Modelo {
constexpr double PI=3.14159265358979323846;
using Vec=std::vector<double>;
struct Signal { Vec t,y,f,m; };
struct Oscillator { Vec t,x,v; };
struct SVD { Eigen::MatrixXd A,U,Vt; Eigen::VectorXd s; };
struct Approximation { Eigen::MatrixXd Ak; double error,reduction; std::size_t bytes; };
inline void finite(double x,const char* name) {
    if(!std::isfinite(x)) throw std::invalid_argument(std::string(name)+": número no finito.");
}
inline std::pair<Vec,Vec> spectrum(const Vec& y,double fs) {
    finite(fs,"Muestreo");
    if(fs<=0 || y.size()<2) throw std::invalid_argument("FFT: señal insuficiente o fs inválido.");
    for(double x:y) finite(x,"Señal");
    Eigen::FFT<double> fft;
    std::vector<std::complex<double>> z;
    fft.fwd(z,y);
    std::size_t n=y.size(),k=n/2+1;
    Vec f(k),m(k);
    for(std::size_t i=0;i<k;++i) {
        f[i]=i*fs/n; m[i]=std::abs(z[i])/n;
        if(i>0 && !(n%2==0 && i==n/2)) m[i]*=2;
    }
    return {std::move(f),std::move(m)};
}
inline Signal signal(double f,double fs,double duration) {
    finite(f,"Frecuencia"); finite(fs,"Muestreo"); finite(duration,"Duración");
    if(f<=0 || fs<=0 || duration<=0) throw std::invalid_argument("Los parámetros deben ser positivos.");
    if(fs<=2*f) throw std::invalid_argument("Nyquist: fs debe ser estrictamente mayor que 2*f.");
    double count=fs*duration;
    if(!std::isfinite(count) || count<2 || count>1e6) throw std::invalid_argument("Se requieren entre 2 y 1 000 000 de muestras.");
    int n=static_cast<int>(std::floor(count+.5)); Signal r; r.t.resize(n);r.y.resize(n);
    for(int i=0;i<n;++i) { r.t[i]=i/fs; r.y[i]=std::sin(2*PI*f*r.t[i]); }
    auto fm=spectrum(r.y,fs);r.f=std::move(fm.first);r.m=std::move(fm.second);return r;
}
inline Oscillator oscillator(double f,double z,double v0,double x0=1) {
    finite(f,"Frecuencia");finite(z,"Zeta");finite(v0,"Velocidad");finite(x0,"Desplazamiento");
    if(f<=0 || f>50) throw std::invalid_argument("Frecuencia natural: 0 < f <= 50 Hz.");
    if(z<0 || z>=1) throw std::invalid_argument("Solo régimen subamortiguado: 0 <= zeta < 1.");
    if(std::abs(v0)>1e6 || std::abs(x0)>1e6) throw std::invalid_argument("Condiciones iniciales fuera de rango.");
    Oscillator r;r.t.resize(2000);r.x.resize(2000);r.v.resize(2000);
    double wn=2*PI*f,a=z*wn,wd=wn*std::sqrt((1-z)*(1+z));
    for(int i=0;i<2000;++i) {
        double t=5.*i/1999,u=wd*t;
        double q=t*(std::abs(u)<1e-8 ? 1-u*u/6 : std::sin(u)/u);
        double e=std::exp(-a*t),c=std::cos(u);
        r.t[i]=t;r.x[i]=e*(x0*c+(v0+a*x0)*q);r.v[i]=e*(v0*c-(wn*wn*x0+a*v0)*q);
        finite(r.x[i],"Resultado x");finite(r.v[i],"Resultado v");
    }
    return r;
}
inline SVD factorize(int n) {
    if(n<10 || n>1000) throw std::invalid_argument("Dimensión entre 10 y 1000.");
    SVD r;r.A.resize(n,n);
    std::mt19937 rng(2026+n);std::normal_distribution<double> normal;
    for(int j=0;j<n;++j) for(int i=0;i<n;++i) r.A(i,j)=normal(rng);
    Eigen::JacobiSVD<Eigen::MatrixXd> svd(r.A,Eigen::ComputeThinU|Eigen::ComputeThinV);
    r.U=svd.matrixU();r.s=svd.singularValues();r.Vt=svd.matrixV().transpose();
    return r;
}
inline Approximation reconstruct(const SVD& r,int k) {
    int n=r.A.rows();
    if(k<1 || k>n/10) throw std::invalid_argument("Rango: 1 <= k <= floor(n/10).");
    Approximation a;
    a.Ak=r.U.leftCols(k)*r.s.head(k).asDiagonal()*r.Vt.topRows(k);
    double norm=r.A.norm();a.error=norm==0 ? 0 : (r.A-a.Ak).norm()/norm;
    a.reduction=100*(1-(2.*n*k+k)/(n*n));
    a.bytes=8*(r.A.size()+r.U.size()+r.s.size()+r.Vt.size()+a.Ak.size());
    return a;
}
}
