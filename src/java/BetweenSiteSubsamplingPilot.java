import java.nio.file.*;
import java.io.*;
import java.util.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

/** Synthetic calibration only. Whole joint tuples in contiguous physical-time blocks. */
public class BetweenSiteSubsamplingPilot {
  static class MI extends MutualInfoCalculatorMultiVariateKraskov1 {
    void temporal(int[] t)throws Exception{ensureKdTreesConstructed();for(int i=0;i<t.length;i+=Math.max(1,t.length/12))for(NeighbourNodeData p:kdTreeJoint.findKNearestNeighbours(4,i,45))if(Math.abs(t[i]-t[p.sampleIndex])<=45)throw new AssertionError("Invalid MI neighbour");}
  }
  static class CMI extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
    void dimension(int d){if(dimensionsVar1!=d)throw new AssertionError("Wrong source dimensions");}
    void temporal(int[] t)throws Exception{ensureKdTreesConstructed();if(dimensionsVar2!=1||dimensionsCond!=1)throw new AssertionError("Wrong dimensions");for(int i=0;i<t.length;i+=Math.max(1,t.length/12))for(NeighbourNodeData p:kdTreeJoint.findKNearestNeighbours(4,i,45))if(Math.abs(t[i]-t[p.sampleIndex])<=45)throw new AssertionError("Invalid CMI neighbour");}
  }
  static double[][] read(String file)throws Exception{
    List<String> lines=Files.readAllLines(Path.of(file));double[][] d=new double[lines.size()][6];
    for(int i=0;i<d.length;i++){String[] a=lines.get(i).split(",");for(int j=0;j<6;j++)d[i][j]=Double.parseDouble(a[j]);}return d;
  }
  static double[][] subset(double[][] d,int start,int stop){
    ArrayList<double[]> rows=new ArrayList<>();for(double[] r:d)if(r[0]>=start&&r[0]<stop)rows.add(r);
    return rows.toArray(new double[0][]);
  }
  static double[] estimates(double[][] d)throws Exception{
    int n=d.length;int[] t=new int[n];double[][] ho=new double[n][1],hn=new double[n][1],tp=new double[n][1],dir=new double[n][2];
    for(int i=0;i<n;i++){t[i]=(int)d[i][0];ho[i][0]=d[i][1];hn[i][0]=d[i][2];tp[i][0]=d[i][3];dir[i][0]=d[i][4];dir[i][1]=d[i][5];}
    MI mi=new MI();SharedEstimatorSettings.apply(mi);ElapsedHourLoader.load(mi,t,ho,hn,4,45);SharedEstimatorSettings.verify(mi);mi.temporal(t);
    CMI period=new CMI();SharedEstimatorSettings.apply(period);ElapsedHourLoader.load(period,t,tp,hn,ho,4,45);SharedEstimatorSettings.verify(period);period.temporal(t);
    CMI direction=new CMI();SharedEstimatorSettings.apply(direction);ElapsedHourLoader.load(direction,t,dir,hn,ho,4,45);SharedEstimatorSettings.verify(direction);direction.temporal(t);direction.dimension(2);period.dimension(1);
    return new double[]{mi.computeAverageLocalOfObservations(),period.computeAverageLocalOfObservations(),direction.computeAverageLocalOfObservations()};
  }
  static void emit(PrintWriter out,int draw,String site,double[][] d)throws Exception{
    double[] values=estimates(d);out.printf(Locale.ROOT,"%d,%s,%d,%.17g,%.17g,%.17g,true%n",draw,site,d.length,values[0],values[1],values[2]);
  }
  public static void main(String[] args)throws Exception{
    for(String job:Files.readAllLines(Path.of(args[0]))){
      String[] f=job.split("\t");double[][] a=read(f[0]),b=read(f[1]);List<String> blocks=Files.readAllLines(Path.of(f[2]));
      try(PrintWriter out=new PrintWriter(f[3])){
        out.println("draw,site,n,height_nats,period_nats,direction_nats,exact_time_verified");emit(out,-1,"A",a);emit(out,-1,"B",b);
        for(int i=0;i<blocks.size();i++){String[] w=blocks.get(i).split(",");emit(out,i,"A",subset(a,Integer.parseInt(w[0]),Integer.parseInt(w[1])));emit(out,i,"B",subset(b,Integer.parseInt(w[2]),Integer.parseInt(w[3])));}
      }
      System.out.println(f[3]);
    }
  }
}
