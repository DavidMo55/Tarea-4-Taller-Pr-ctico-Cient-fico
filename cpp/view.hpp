#pragma once
#include <QtWidgets>
#include <cmath>
#include <vector>

// Vista: dibuja puntos y controles, sin calcular FFT ni SVD.
class PlotWidget : public QWidget {
    std::vector<double> xs,ys;
    QString title,xlabel,ylabel;
    bool logx=false,logy=false;
    double cutoff=-1;
public:
    PlotWidget(QWidget* parent=nullptr):QWidget(parent) { setMinimumSize(320,240); }
    void setData(const std::vector<double>& x,const std::vector<double>& y,QString titulo,QString ex,QString ey,
                 bool lx=false,bool ly=false,double corte=-1) {
        xs.clear();ys.clear();
        if(x.size()!=y.size()) {update();return;}
        // Envolvente min/max para dibujar como máximo ~6000 puntos sin perder picos.
        std::size_t block=std::max<std::size_t>(1,(x.size()+2999)/3000);
        for(std::size_t lo=0;lo<x.size();lo+=block) {
            std::size_t hi=std::min(x.size(),lo+block),imin=lo,imax=lo;
            for(std::size_t j=lo+1;j<hi;++j) {if(y[j]<y[imin])imin=j;if(y[j]>y[imax])imax=j;}
            std::size_t first=std::min(imin,imax),second=std::max(imin,imax);
            xs.push_back(x[first]);ys.push_back(y[first]);
            if(first!=second) {xs.push_back(x[second]);ys.push_back(y[second]);}
        }
        title=titulo;xlabel=ex;ylabel=ey;logx=lx;logy=ly;cutoff=corte;update();
    }
    void paintEvent(QPaintEvent*) override {
        QPainter p(this);p.setRenderHint(QPainter::Antialiasing);p.fillRect(rect(),Qt::white);
        QRectF area(100,48,width()-150,height()-102);
        p.setPen(QColor("#263747"));p.drawText(QRectF(12,8,width()-24,30),Qt::AlignCenter,title);
        p.drawText(QRectF(60,height()-28,width()-80,22),Qt::AlignCenter,xlabel);
        p.save();p.translate(12,height()/2);p.rotate(-90);p.drawText(QRectF(-110,-10,220,22),Qt::AlignCenter,ylabel);p.restore();
        if(xs.empty() || xs.size()!=ys.size()) return;
        std::vector<QPointF> data;data.reserve(xs.size());
        double xmin=INFINITY,xmax=-INFINITY,ymin=INFINITY,ymax=-INFINITY;
        for(std::size_t i=0;i<xs.size();++i) {
            if((logx && xs[i]<=0)||(logy && ys[i]<=0)) continue;
            double x=logx?std::log10(xs[i]):xs[i],y=logy?std::log10(ys[i]):ys[i];
            if(!std::isfinite(x)||!std::isfinite(y)) continue;
            data.emplace_back(x,y);xmin=std::min(xmin,x);xmax=std::max(xmax,x);ymin=std::min(ymin,y);ymax=std::max(ymax,y);
        }
        if(data.empty()) return;
        if(xmax==xmin) xmax=xmin+1;
        if(ymax==ymin) {ymin-=.5;ymax+=.5;}
        double pad=.05*(ymax-ymin);ymin-=pad;ymax+=pad;
        auto map=[&](QPointF d){return QPointF(area.left()+(d.x()-xmin)/(xmax-xmin)*area.width(),area.bottom()-(d.y()-ymin)/(ymax-ymin)*area.height());};
        for(int i=0;i<=4;++i) {
            double q=i/4.,x=xmin+q*(xmax-xmin),y=ymin+q*(ymax-ymin);
            double xx=area.left()+q*area.width(),yy=area.bottom()-q*area.height();
            p.setPen(QColor("#e3e9ed"));p.drawLine(QPointF(xx,area.top()),QPointF(xx,area.bottom()));p.drawLine(QPointF(area.left(),yy),QPointF(area.right(),yy));
            p.setPen(QColor("#455966"));
            p.drawText(QRectF(xx-36,area.bottom()+5,72,20),Qt::AlignCenter,QString::number(logx?std::pow(10,x):x,'g',3));
            p.drawText(QRectF(25,yy-10,68,20),Qt::AlignRight|Qt::AlignVCenter,QString::number(logy?std::pow(10,y):(std::abs(y)<1e-12?0:y),'g',3));
        }
        p.save();p.setClipRect(area);QPainterPath path;path.moveTo(map(data.front()));
        // Limitar solo los puntos dibujados; los modelos conservan todos los datos.
        std::size_t step=1;
        for(std::size_t i=step;i<data.size();i+=step) path.lineTo(map(data[i]));
        path.lineTo(map(data.back()));p.setPen(QPen(QColor("#176e97"),1.6));p.drawPath(path);
        if(cutoff>0) {
            double x=logx?std::log10(cutoff):cutoff;
            QPointF q=map({x,ymin});p.setPen(QPen(QColor("#d16b30"),1.8,Qt::DashLine));p.drawLine(QPointF(q.x(),area.top()),QPointF(q.x(),area.bottom()));
        }
        p.restore();p.setPen(QColor("#8a9aa6"));p.drawRect(area);
    }
};

class LabView:public QWidget {
public:
    QTabWidget* tabs;
    QDoubleSpinBox *freq,*fs,*duration,*natural,*zeta,*velocity;
    QComboBox *scale,*dimension;
    QSlider* rank;
    QPushButton *generate,*simulate,*reset;
    QLabel *fftLabel,*errorLabel,*reductionLabel,*countLabel,*ramLabel,*rankLabel,*status;
    PlotWidget *timePlot,*fftPlot,*responsePlot,*phasePlot,*svdPlot;
    LabView() {
        setWindowTitle("Tarea 4 · Laboratorio MVC · C++ / Qt");resize(1180,740);
        auto root=new QVBoxLayout(this);root->setContentsMargins(18,18,18,14);
        auto title=new QLabel("Laboratorio de señales, dinámica y compresión");
        title->setStyleSheet("font-size:20px;font-weight:600;color:#15394d;padding:8px;");root->addWidget(title);
        tabs=new QTabWidget;root->addWidget(tabs,1);
        auto panel=new QWidget;auto lay=new QVBoxLayout(panel);auto controls=new QHBoxLayout;lay->addLayout(controls);
        freq=number(440,0,1e6,2);fs=number(10000,0,1e6,1);duration=number(1,0,10,4);
        add(controls,"Señal (Hz)",freq);add(controls,"Muestreo fs (Hz)",fs);add(controls,"Duración (s)",duration);
        scale=new QComboBox;scale->addItems({"Lineal","Semilogarítmica"});add(controls,"Escala",scale);
        generate=new QPushButton("Generar y analizar");controls->addWidget(generate);
        auto graphs=new QHBoxLayout;timePlot=new PlotWidget;fftPlot=new PlotWidget;graphs->addWidget(timePlot);graphs->addWidget(fftPlot);lay->addLayout(graphs,1);
        fftLabel=new QLabel;lay->addWidget(fftLabel);tabs->addTab(panel,"Señal y FFT");
        panel=new QWidget;lay=new QVBoxLayout(panel);controls=new QHBoxLayout;lay->addLayout(controls);
        natural=number(2.5,0,100,3);zeta=number(.15,-1,2,5);velocity=number(0,-1e6,1e6,3);
        add(controls,"Frecuencia natural (Hz)",natural);add(controls,"Zeta",zeta);add(controls,"Velocidad inicial",velocity);
        simulate=new QPushButton("Simular");reset=new QPushButton("Restablecer nominales");controls->addWidget(simulate);controls->addWidget(reset);
        graphs=new QHBoxLayout;responsePlot=new PlotWidget;phasePlot=new PlotWidget;graphs->addWidget(responsePlot);graphs->addWidget(phasePlot);lay->addLayout(graphs,1);tabs->addTab(panel,"Oscilador y fase");
        panel=new QWidget;lay=new QVBoxLayout(panel);controls=new QHBoxLayout;lay->addLayout(controls);
        dimension=new QComboBox;dimension->addItems({"100","250","500","1000"});add(controls,"Dimensión n",dimension);
        rank=new QSlider(Qt::Horizontal);rank->setRange(1,10);rank->setValue(1);controls->addWidget(rank,1);
        rankLabel=new QLabel("k = 1");controls->addWidget(rankLabel);
        auto metrics=new QHBoxLayout;errorLabel=metric("Error relativo");reductionLabel=metric("Reducción");countLabel=metric("Ejecuciones SVD");
        for(auto label:{errorLabel,reductionLabel,countLabel}) metrics->addWidget(label,1);
        lay->addLayout(metrics);svdPlot=new PlotWidget;lay->addWidget(svdPlot,1);
        ramLabel=new QLabel;ramLabel->setWordWrap(true);lay->addWidget(ramLabel);tabs->addTab(panel,"Compresión SVD");
        status=new QLabel("Listo");root->addWidget(status);
    }
private:
    static QDoubleSpinBox* number(double value,double min,double max,int decimals) {
        auto w=new QDoubleSpinBox;w->setRange(min,max);w->setDecimals(decimals);w->setValue(value);w->setKeyboardTracking(false);return w;
    }
    static void add(QHBoxLayout* l,const QString& name,QWidget* w) {l->addWidget(new QLabel(name));l->addWidget(w);}
    static QLabel* metric(QString title) {
        auto label=new QLabel(title);label->setMinimumHeight(66);label->setAlignment(Qt::AlignCenter);
        label->setStyleSheet("background:#eaf3f8;color:#15394d;border-radius:8px;padding:10px;font-size:17px;");return label;
    }
};
